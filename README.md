# 🌙 Mond

<div align="center">
  <img src="docs/assets/images/mond-logo.png" alt="Mond Logo" width="300"/>
</div>

> AI-Powered DevSecOps Platform - Illuminating Security in the Cloud

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-Compatible-orange.svg)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

## 📋 Overview

**Mond** (German for "Moon") is an open-source DevSecOps platform that illuminates the path to secure cloud operations. Like the moon guides travelers through the night, Mond provides gentle, intelligent guidance for enterprise security and compliance management in AWS environments.

### 🎯 Mission

Mond transforms security from a barrier into an enabler. We believe security should be:
- **Gentle**: Non-intrusive and developer-friendly
- **Intelligent**: AI-powered recommendations and automation  
- **Illuminating**: Clear visibility into security posture
- **Reliable**: Always there when you need it, like the moon in the night sky

### ✨ Why Mond?

Traditional security tools often create friction in development workflows. Mond takes a different approach - we provide **moonlight-soft guidance** that helps teams navigate security requirements without slowing them down. Our AI-powered tag recommendations and automated compliance monitoring work quietly in the background, ensuring your infrastructure stays secure while your teams stay productive.

### 🎯 Key Features

- **🤖 AI-Powered Tag Recommendations** - Smart tagging with ML-based suggestions
- **🛡️ Integrated Security Dashboard** - Unified AWS security services monitoring
- **🔐 Self-Service Portal** - Automated permission and policy management
- **📊 Advanced Analytics** - Tag-based cost analysis and compliance reporting
- **⚡ Security Automation** - Automated threat detection and response

## 🏗️ Architecture

```mermaid
graph TB
    A[Frontend - React/TypeScript] --> B[API Gateway - FastAPI]
    B --> C[Authentication - AWS Identity Center]
    B --> D[Core Services]
    D --> E[Tag Recommendation Engine]
    D --> F[Security Monitoring]
    D --> G[Compliance Engine]
    D --> H[Workflow Engine]
    
    E --> I[ML Models]
    F --> J[AWS Security Hub]
    F --> K[GuardDuty]
    G --> L[AWS Config]
    H --> M[Approval Workflows]
    
    D --> N[Database - PostgreSQL]
    D --> O[Cache - Redis]
    D --> P[Message Queue - Celery]
```

## 🚀 Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- Docker & Docker Compose
- Python 3.9+
- Node.js 16+

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/jland-93/mond.git
cd mond
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your AWS credentials and configuration
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the platform**
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs

## 📊 Core Modules

### 1. 🏷️ AI-Powered Tag Management

#### Smart Tag Recommendations
- **Real-time Suggestions**: Context-aware tag recommendations during resource creation
- **Pattern Learning**: ML-based analysis of organizational tagging patterns
- **Anomaly Detection**: Automatic detection of tag inconsistencies and duplicates
- **Predictive Tagging**: Lifecycle-based tag suggestions

#### Tag Compliance Dashboard
```typescript
interface TagMetrics {
  complianceScore: number;        // 0-100 tag health score
  mandatoryTagCoverage: number;   // % of resources with required tags
  costVisibility: number;         // % of costs allocated via tags
  policyViolations: TagViolation[];
}
```

### 2. 🛡️ Security Overview Dashboard

#### Integrated Security Monitoring
- **AWS Security Hub** - Centralized security findings
- **GuardDuty Integration** - Threat detection and response
- **Config Rules** - Compliance monitoring
- **Certificate Management** - SSL/TLS certificate tracking

#### Real-time Security Metrics
```python
class SecurityMetrics:
    def __init__(self):
        self.security_score = self.calculate_security_score()
        self.active_threats = self.get_active_threats()
        self.compliance_status = self.get_compliance_status()
        self.certificate_status = self.get_certificate_status()
```

### 3. 🔐 Self-Service Portal

#### Permission Management
- **Identity Center Integration** - SSO and permission set management
- **Temporary Privilege Escalation** - Break-glass access workflows
- **Cross-Account Access** - Multi-account permission requests
- **Resource-specific Permissions** - Granular access control

#### Policy Management
- **Security Group Rules** - Automated rule change requests
- **WAF Configuration** - Whitelist and rule management
- **S3 Bucket Policies** - Policy change workflows
- **KMS Key Access** - Encryption key permission management

### 4. 📈 Advanced Analytics

#### Tag-based Cost Analysis
```sql
-- Example: Cost allocation by tags
SELECT 
    tag_project,
    tag_environment,
    SUM(cost) as total_cost,
    COUNT(resources) as resource_count
FROM cost_allocation 
WHERE date >= '2024-01-01'
GROUP BY tag_project, tag_environment;
```

#### Compliance Reporting
- **Automated Reports** - Scheduled compliance reports
- **Audit Trails** - Complete change history
- **Risk Assessment** - Security risk scoring
- **Trend Analysis** - Historical compliance trends

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL + InfluxDB
- **Cache**: Redis
- **Message Queue**: Celery
- **ML Engine**: scikit-learn, TensorFlow

### Frontend
- **Framework**: React + TypeScript
- **UI Library**: Ant Design
- **Visualization**: Chart.js, D3.js
- **State Management**: Redux Toolkit

### Infrastructure
- **Container**: Amazon EKS
- **Database**: Amazon RDS PostgreSQL
- **Cache**: Amazon ElastiCache
- **Load Balancer**: Application Load Balancer
- **Storage**: Amazon S3, EFS

### AWS Services Integration
```yaml
Security:
  - AWS Security Hub
  - Amazon GuardDuty
  - AWS Config
  - AWS Inspector
  
Identity:
  - AWS Identity Center
  - AWS IAM
  
Monitoring:
  - Amazon CloudWatch
  - AWS CloudTrail
  - AWS X-Ray
  
Cost Management:
  - AWS Cost Explorer
  - AWS Budgets
  - Cost Anomaly Detection
```

## 📱 Screenshots

### 🌙 Mond Dashboard
![Mond Dashboard](docs/assets/images/mond-dashboard.png)
*Main security overview with moonlight-themed UI*

### 🏷️ AI Tag Recommendations
![Tag Recommendations](docs/assets/images/tag-recommendations.png)
*Intelligent tag suggestions powered by ML*

### 🔐 Self-Service Portal
![Self Service Portal](docs/assets/images/self-service-portal.png)
*Developer-friendly security request workflows*

### 📊 Analytics & Insights
![Analytics Dashboard](docs/assets/images/analytics-dashboard.png)
*Tag-based cost analysis and compliance reporting*

## 🔧 Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/devsecops
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# Tag Recommendation Engine
ML_MODEL_PATH=/app/models/tag_recommendation.pkl
RECOMMENDATION_CONFIDENCE_THRESHOLD=0.8
```

### Tag Policies Configuration
```yaml
# config/tag_policies.yaml
mandatory_tags:
  - Environment
  - Owner
  - Project
  - CostCenter

conditional_tags:
  Production:
    - BackupSchedule
    - MonitoringLevel
  Database:
    - EncryptionKey
    - RetentionPeriod

format_rules:
  Environment: "^(dev|staging|prod)$"
  CostCenter: "^CC-[0-9]{4}$"
  Owner: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
```

## 📊 Metrics & KPIs

### Security Metrics
- **Security Score**: Overall security posture (0-100)
- **MTTR**: Mean Time To Resolve security issues
- **Compliance Rate**: Percentage of compliant resources
- **Automation Coverage**: Percentage of automated security checks

### Tag Management Metrics
- **Tag Coverage**: Percentage of resources with required tags
- **Tag Consistency**: Tag standardization score
- **Cost Visibility**: Percentage of costs allocated via tags
- **Time Savings**: Reduction in manual tagging effort

### Operational Metrics
- **Request Processing Time**: Average approval workflow duration
- **Self-Service Adoption**: Percentage of automated requests
- **User Satisfaction**: Platform usability score
- **API Performance**: Response time and availability

## 🚀 Roadmap

### Phase 1: MVP (Q1 2024)
- [x] Basic dashboard and AWS integration
- [x] Tag recommendation engine foundation
- [x] Permission request workflows
- [x] Security monitoring basics

### Phase 2: Enhancement (Q2 2024)
- [ ] Advanced ML-based tag recommendations
- [ ] Automated security response system
- [ ] Advanced analytics and reporting
- [ ] Mobile application support

### Phase 3: Scale (Q3 2024)
- [ ] Multi-cloud support (Azure, GCP)
- [ ] Advanced ML anomaly detection
- [ ] API ecosystem and integrations
- [ ] Community features and marketplace

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
npm start

# Run tests
pytest backend/tests/
npm test --prefix frontend/
```

### Code Style
- **Python**: Black, isort, flake8
- **TypeScript**: ESLint, Prettier
- **Commit Messages**: Conventional Commits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.mond.dev](https://docs.mond.dev)
- **Issues**: [GitHub Issues](https://github.com/jland-93/mond/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jland-93/mond/discussions)
- **Slack**: [Join our Slack](https://slack.mond.dev)

## 🙏 Acknowledgments

- AWS Security Best Practices
- OWASP DevSecOps Guidelines
- Cloud Security Alliance (CSA)
- Open Source Security Foundation (OpenSSF)

---

**Made with 🌙 by jland - Illuminating the path to secure DevOps**
