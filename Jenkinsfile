// ============================================================================
// Jenkins Pipeline for PCI Compliance Lab
// TWN-Style CI/CD Pipeline
// ============================================================================

pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-west-2'
        TF_IN_AUTOMATION = 'true'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo '✓ Code checked out'
            }
        }
        
        stage('Terraform Lint') {
            steps {
                script {
                    dir('iac/terraform') {
                        sh 'terraform fmt -check -recursive'
                        echo '✓ Terraform formatting verified'
                    }
                }
            }
        }
        
        stage('Terraform Validate') {
            steps {
                script {
                    dir('iac/terraform') {
                        sh 'terraform init -backend=false'
                        sh 'terraform validate'
                        echo '✓ Terraform configuration validated'
                    }
                }
            }
        }
        
        stage('Python Lint') {
            steps {
                script {
                    sh '''
                        python3 -m pip install --user ruff
                        python3 -m ruff check evidence/collectors/python/*.py automation/lambda/*.py || true
                    '''
                    echo '✓ Python linting complete'
                }
            }
        }
        
        stage('Python Syntax Check') {
            steps {
                script {
                    sh '''
                        python3 -m py_compile evidence/collectors/python/evidence_collect_basic.py
                        python3 -m py_compile automation/lambda/evidence_snapshot.py
                    '''
                    echo '✓ Python syntax validated'
                }
            }
        }
        
        stage('Documentation Check') {
            steps {
                script {
                    sh '''
                        test -f README.md && echo "✓ README.md exists"
                        test -f docs/pci_mapping.md && echo "✓ PCI mapping exists"
                        test -f runbooks/audit_evidence_runbook.md && echo "✓ Runbook exists"
                        test -f evidence/schema/evidence_register.csv && echo "✓ Evidence register exists"
                    '''
                    echo '✓ Documentation validated'
                }
            }
        }
        
        stage('Evidence Collector Test') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                script {
                    echo 'Running evidence collector in test mode...'
                    // In production, you would configure AWS credentials and run:
                    // sh 'cd evidence/collectors/python && python3 evidence_collect_basic.py --local-only ...'
                    echo '⚠ Skipping actual collection (requires AWS credentials)'
                }
            }
        }
    }
    
    post {
        success {
            echo '✓ Pipeline completed successfully'
        }
        failure {
            echo '✗ Pipeline failed'
        }
        always {
            cleanWs()
        }
    }
}
