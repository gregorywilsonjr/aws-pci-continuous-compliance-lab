#!/usr/bin/env python3
"""
============================================================================
PCI DSS Evidence Collector - Basic Manual Collection
============================================================================
WHAT: Manual evidence collector for IAM MFA, policies, and CloudTrail
WHY: Demonstrates targeted artifact collection for Req. 7, 8, 10
USAGE: ./evidence_collect_basic.py --region us-west-2 --evidence-bucket <BUCKET> --prefix baseline/2024-01-15
============================================================================
"""

import argparse
import json
import os
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError


def main():
    parser = argparse.ArgumentParser(
        description='Collect PCI DSS evidence artifacts for IAM and CloudTrail'
    )
    parser.add_argument('--region', required=True, help='AWS region')
    parser.add_argument('--evidence-bucket', required=True, help='S3 bucket for evidence')
    parser.add_argument('--prefix', required=True, help='S3 prefix (e.g., baseline/2024-01-15)')
    parser.add_argument('--local-only', action='store_true', help='Save locally only, do not upload to S3')
    
    args = parser.parse_args()
    
    # Initialize AWS clients
    iam_client = boto3.client('iam', region_name=args.region)
    cloudtrail_client = boto3.client('cloudtrail', region_name=args.region)
    s3_client = boto3.client('s3', region_name=args.region)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    print(f"\n{'='*70}")
    print(f"PCI DSS Evidence Collection")
    print(f"Timestamp: {timestamp}")
    print(f"Region: {args.region}")
    print(f"Evidence Bucket: {args.evidence_bucket}")
    print(f"Prefix: {args.prefix}")
    print(f"{'='*70}\n")
    
    # Collection results
    results = {
        'timestamp': timestamp,
        'region': args.region,
        'artifacts': []
    }
    
    # 1. Collect IAM MFA Status (Req. 8 - Multi-Factor Authentication)
    print("[1/3] Collecting IAM MFA status (PCI Req. 8)...")
    try:
        mfa_data = collect_iam_mfa_status(iam_client)
        filename = 'iam_mfa_status.json'
        save_artifact(filename, mfa_data)
        
        if not args.local_only:
            s3_key = f"{args.prefix}/{filename}"
            upload_to_s3(s3_client, args.evidence_bucket, s3_key, mfa_data)
            results['artifacts'].append(s3_key)
        
        print(f"  ✓ Collected MFA status for {mfa_data['total_users']} users")
        print(f"    - With MFA: {mfa_data['users_with_mfa']}")
        print(f"    - Without MFA: {mfa_data['users_without_mfa']}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        results['mfa_error'] = str(e)
    
    # 2. Collect IAM Role Policies (Req. 7 - Least Privilege)
    print("\n[2/3] Collecting IAM role policies (PCI Req. 7)...")
    try:
        policies_data = collect_iam_role_policies(iam_client)
        filename = 'iam_role_policies.json'
        save_artifact(filename, policies_data)
        
        if not args.local_only:
            s3_key = f"{args.prefix}/{filename}"
            upload_to_s3(s3_client, args.evidence_bucket, s3_key, policies_data)
            results['artifacts'].append(s3_key)
        
        print(f"  ✓ Collected policies for {policies_data['total_roles']} roles")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        results['policies_error'] = str(e)
    
    # 3. Collect Recent CloudTrail Events (Req. 10 - Audit Logging)
    print("\n[3/3] Collecting recent CloudTrail events (PCI Req. 10)...")
    try:
        cloudtrail_data = collect_cloudtrail_events(cloudtrail_client, days=7)
        filename = 'cloudtrail_recent_events.json'
        save_artifact(filename, cloudtrail_data)
        
        if not args.local_only:
            s3_key = f"{args.prefix}/{filename}"
            upload_to_s3(s3_client, args.evidence_bucket, s3_key, cloudtrail_data)
            results['artifacts'].append(s3_key)
        
        print(f"  ✓ Collected {cloudtrail_data['total_events']} events from last 7 days")
        print(f"    - Admin events: {cloudtrail_data['admin_events_count']}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        results['cloudtrail_error'] = str(e)
    
    # Save collection summary
    summary_filename = 'collection_summary.json'
    save_artifact(summary_filename, results)
    
    if not args.local_only:
        s3_key = f"{args.prefix}/{summary_filename}"
        upload_to_s3(s3_client, args.evidence_bucket, s3_key, results)
    
    print(f"\n{'='*70}")
    print("✓ Evidence collection complete!")
    print(f"{'='*70}\n")
    
    if not args.local_only:
        print(f"Artifacts uploaded to s3://{args.evidence_bucket}/{args.prefix}/")
    else:
        print("Artifacts saved locally only (--local-only flag set)")


def collect_iam_mfa_status(iam_client):
    """
    Collect MFA status for all IAM users.
    
    WHY: PCI Req. 8.3.1 - Multi-factor authentication for all non-console
         administrative access and all remote access to the CDE
    """
    
    mfa_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_users': 0,
        'users_with_mfa': 0,
        'users_without_mfa': 0,
        'users': []
    }
    
    # List all IAM users
    paginator = iam_client.get_paginator('list_users')
    
    for page in paginator.paginate():
        for user in page['Users']:
            username = user['UserName']
            mfa_data['total_users'] += 1
            
            # Check for MFA devices
            mfa_devices = iam_client.list_mfa_devices(UserName=username)
            has_mfa = len(mfa_devices['MFADevices']) > 0
            
            if has_mfa:
                mfa_data['users_with_mfa'] += 1
            else:
                mfa_data['users_without_mfa'] += 1
            
            user_info = {
                'UserName': username,
                'UserId': user['UserId'],
                'CreateDate': user['CreateDate'].isoformat(),
                'HasMFA': has_mfa,
                'MFADevices': [
                    {
                        'SerialNumber': device['SerialNumber'],
                        'EnableDate': device['EnableDate'].isoformat()
                    }
                    for device in mfa_devices['MFADevices']
                ]
            }
            
            # Check password last used
            if 'PasswordLastUsed' in user:
                user_info['PasswordLastUsed'] = user['PasswordLastUsed'].isoformat()
            
            mfa_data['users'].append(user_info)
    
    return mfa_data


def collect_iam_role_policies(iam_client):
    """
    Collect IAM role policies for least privilege review.
    
    WHY: PCI Req. 7.2.1 - Access control systems ensure access is based on
         need to know and is set to "deny all" unless specifically allowed
    """
    
    policies_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_roles': 0,
        'roles': []
    }
    
    # List all IAM roles
    paginator = iam_client.get_paginator('list_roles')
    
    for page in paginator.paginate():
        for role in page['Roles']:
            role_name = role['RoleName']
            policies_data['total_roles'] += 1
            
            role_info = {
                'RoleName': role_name,
                'RoleId': role['RoleId'],
                'CreateDate': role['CreateDate'].isoformat(),
                'ManagedPolicies': [],
                'InlinePolicies': []
            }
            
            # Get attached managed policies
            try:
                attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
                for policy in attached_policies['AttachedPolicies']:
                    role_info['ManagedPolicies'].append({
                        'PolicyName': policy['PolicyName'],
                        'PolicyArn': policy['PolicyArn']
                    })
            except ClientError as e:
                role_info['ManagedPoliciesError'] = str(e)
            
            # Get inline policies
            try:
                inline_policies = iam_client.list_role_policies(RoleName=role_name)
                for policy_name in inline_policies['PolicyNames']:
                    policy_doc = iam_client.get_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name
                    )
                    role_info['InlinePolicies'].append({
                        'PolicyName': policy_name,
                        'PolicyDocument': policy_doc['PolicyDocument']
                    })
            except ClientError as e:
                role_info['InlinePoliciesError'] = str(e)
            
            policies_data['roles'].append(role_info)
    
    return policies_data


def collect_cloudtrail_events(cloudtrail_client, days=7):
    """
    Collect recent CloudTrail events for audit logging.
    
    WHY: PCI Req. 10.2 - Implement automated audit trails for all system
         components to reconstruct administrative actions
    """
    
    cloudtrail_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'lookback_days': days,
        'total_events': 0,
        'admin_events_count': 0,
        'events': []
    }
    
    # Calculate start time
    start_time = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Lookup events (focus on admin/write events)
    try:
        paginator = cloudtrail_client.get_paginator('lookup_events')
        page_iterator = paginator.paginate(
            LookupAttributes=[
                {
                    'AttributeKey': 'ReadOnly',
                    'AttributeValue': 'false'
                }
            ],
            StartTime=start_time,
            MaxResults=50
        )
        
        for page in page_iterator:
            for event in page.get('Events', []):
                cloudtrail_data['total_events'] += 1
                
                # Check if admin event
                event_name = event.get('EventName', '')
                if any(admin_term in event_name.lower() for admin_term in ['create', 'delete', 'update', 'put', 'attach', 'detach']):
                    cloudtrail_data['admin_events_count'] += 1
                
                event_info = {
                    'EventId': event.get('EventId'),
                    'EventName': event.get('EventName'),
                    'EventTime': event.get('EventTime').isoformat(),
                    'Username': event.get('Username'),
                    'ResourceType': event.get('ResourceType'),
                    'ResourceName': event.get('ResourceName')
                }
                
                cloudtrail_data['events'].append(event_info)
                
                # Limit to 100 events in output
                if cloudtrail_data['total_events'] >= 100:
                    break
            
            if cloudtrail_data['total_events'] >= 100:
                break
    
    except ClientError as e:
        cloudtrail_data['error'] = str(e)
    
    return cloudtrail_data


def save_artifact(filename, data):
    """Save artifact to local file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  → Saved locally: {filename}")


def upload_to_s3(s3_client, bucket, key, data):
    """Upload artifact to S3."""
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType='application/json',
        ServerSideEncryption='AES256'
    )
    print(f"  → Uploaded to S3: s3://{bucket}/{key}")


if __name__ == '__main__':
    main()
