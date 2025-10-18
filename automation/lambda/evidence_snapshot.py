#!/usr/bin/env python3
"""
============================================================================
AWS PCI DSS Evidence Snapshot Lambda
============================================================================
WHAT: Daily snapshot of Security Hub findings and AWS Config compliance
WHY: Provides timestamped, auditor-friendly evidence artifacts
TRIGGERED BY: EventBridge (CloudWatch Events) daily schedule
============================================================================
"""

import json
import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# Environment variables
EVIDENCE_BUCKET = os.environ.get('EVIDENCE_BUCKET')
REGION = os.environ.get('REGION', 'us-west-2')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=REGION)
securityhub_client = boto3.client('securityhub', region_name=REGION)
config_client = boto3.client('config', region_name=REGION)


def lambda_handler(event, context):
    """
    Main Lambda handler for daily evidence snapshot.
    
    Collects:
    - Security Hub findings summary
    - AWS Config rules compliance status
    
    Uploads to S3: artifacts/daily/YYYY-MM-DD/
    """
    
    if not EVIDENCE_BUCKET:
        return {
            'statusCode': 500,
            'body': json.dumps('ERROR: EVIDENCE_BUCKET environment variable not set')
        }
    
    # Generate timestamp and S3 prefix
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d')
    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    s3_prefix = f"artifacts/daily/{date_str}"
    
    results = {
        'timestamp': timestamp_str,
        'region': REGION,
        'artifacts': []
    }
    
    # Collect Security Hub findings
    try:
        sh_summary = collect_securityhub_findings()
        sh_key = f"{s3_prefix}/securityhub_findings_summary.json"
        upload_to_s3(sh_key, sh_summary)
        results['artifacts'].append(sh_key)
        print(f"✓ Uploaded Security Hub summary to {sh_key}")
    except Exception as e:
        print(f"✗ Error collecting Security Hub findings: {str(e)}")
        results['securityhub_error'] = str(e)
    
    # Collect AWS Config compliance
    try:
        config_summary = collect_config_compliance()
        config_key = f"{s3_prefix}/aws_config_rules_brief.json"
        upload_to_s3(config_key, config_summary)
        results['artifacts'].append(config_key)
        print(f"✓ Uploaded Config compliance to {config_key}")
    except Exception as e:
        print(f"✗ Error collecting Config compliance: {str(e)}")
        results['config_error'] = str(e)
    
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }


def collect_securityhub_findings():
    """
    Collect Security Hub findings summary.
    
    Returns aggregated counts by severity and compliance status.
    """
    
    findings_summary = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'region': REGION,
        'total_findings': 0,
        'by_severity': {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'INFORMATIONAL': 0
        },
        'by_compliance_status': {
            'PASSED': 0,
            'FAILED': 0,
            'WARNING': 0,
            'NOT_AVAILABLE': 0
        },
        'sample_findings': []
    }
    
    # Get findings (paginated)
    paginator = securityhub_client.get_paginator('get_findings')
    page_iterator = paginator.paginate(
        Filters={
            'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}]
        },
        MaxResults=100
    )
    
    finding_count = 0
    for page in page_iterator:
        for finding in page.get('Findings', []):
            finding_count += 1
            
            # Count by severity
            severity = finding.get('Severity', {}).get('Label', 'INFORMATIONAL')
            findings_summary['by_severity'][severity] = findings_summary['by_severity'].get(severity, 0) + 1
            
            # Count by compliance status
            compliance_status = finding.get('Compliance', {}).get('Status', 'NOT_AVAILABLE')
            findings_summary['by_compliance_status'][compliance_status] = findings_summary['by_compliance_status'].get(compliance_status, 0) + 1
            
            # Collect sample findings (first 10)
            if len(findings_summary['sample_findings']) < 10:
                findings_summary['sample_findings'].append({
                    'Id': finding.get('Id'),
                    'Title': finding.get('Title'),
                    'Severity': severity,
                    'ComplianceStatus': compliance_status,
                    'ResourceType': finding.get('Resources', [{}])[0].get('Type', 'Unknown')
                })
    
    findings_summary['total_findings'] = finding_count
    
    return findings_summary


def collect_config_compliance():
    """
    Collect AWS Config rules compliance status.
    
    Returns summary of compliant vs non-compliant rules.
    """
    
    config_summary = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'region': REGION,
        'total_rules': 0,
        'by_compliance': {
            'COMPLIANT': 0,
            'NON_COMPLIANT': 0,
            'NOT_APPLICABLE': 0,
            'INSUFFICIENT_DATA': 0
        },
        'rules': []
    }
    
    # Get all Config rules
    try:
        rules_response = config_client.describe_config_rules()
        config_rules = rules_response.get('ConfigRules', [])
        config_summary['total_rules'] = len(config_rules)
        
        # Get compliance status for each rule
        for rule in config_rules:
            rule_name = rule['ConfigRuleName']
            
            try:
                compliance_response = config_client.describe_compliance_by_config_rule(
                    ConfigRuleNames=[rule_name]
                )
                
                for compliance in compliance_response.get('ComplianceByConfigRules', []):
                    compliance_type = compliance.get('Compliance', {}).get('ComplianceType', 'INSUFFICIENT_DATA')
                    
                    config_summary['by_compliance'][compliance_type] = config_summary['by_compliance'].get(compliance_type, 0) + 1
                    
                    config_summary['rules'].append({
                        'RuleName': rule_name,
                        'ComplianceType': compliance_type,
                        'Description': rule.get('Description', '')
                    })
            except ClientError as e:
                print(f"Warning: Could not get compliance for rule {rule_name}: {str(e)}")
                config_summary['rules'].append({
                    'RuleName': rule_name,
                    'ComplianceType': 'ERROR',
                    'Error': str(e)
                })
    
    except ClientError as e:
        print(f"Error describing Config rules: {str(e)}")
        config_summary['error'] = str(e)
    
    return config_summary


def upload_to_s3(key, data):
    """
    Upload JSON data to S3 evidence bucket.
    
    Args:
        key: S3 object key
        data: Dictionary to serialize as JSON
    """
    
    s3_client.put_object(
        Bucket=EVIDENCE_BUCKET,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType='application/json',
        ServerSideEncryption='AES256'
    )


# For local testing
if __name__ == '__main__':
    # Mock event and context
    test_event = {}
    test_context = type('Context', (), {
        'function_name': 'test-function',
        'memory_limit_in_mb': 128,
        'invoked_function_arn': 'arn:aws:lambda:us-west-2:123456789012:function:test',
        'aws_request_id': 'test-request-id'
    })()
    
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
