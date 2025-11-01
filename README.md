# EVM Project Budget Management System

## High-Level Goal

The **EVM Project Budget Management System** is a comprehensive application designed for the Project Management Directorate to simulate, test, and validate financial management processes for end-of-line automation projects before implementing them in production environments.

The system enables organizations to:

- Model complex project scenarios with multiple machines (WBEs) and departmental cost elements
- Track project financial performance using Earned Value Management (EVM) principles
- Validate business rules and performance metrics under various conditions
- Support complete project lifecycle financial management including budgets, costs, forecasts, change orders, and quality events
- Generate accurate EVM calculations and reports for decision-making

This tool serves as a simulation and validation platform, allowing the Project Management Directorate to refine business rules, test performance metrics, and establish best practices for project financial management without impacting production systems.

## Documentation Structure

All project documentation is located in the [`docs/`](docs/) directory:

### Core Documentation

- **[`prd.md`](docs/prd.md)** - Product Requirements Document
  - Comprehensive requirements specification
  - Business context and objectives
  - System capabilities and features
  - EVM calculation requirements
  - User interface and reporting requirements

- **[`plan.md`](docs/plan.md)** - Project Plan and MVP Development Roadmap
  - Executive summary and development approach
  - Epic breakdown (5 major epics)
  - Sprint plan overview (6 two-week sprints)
  - MVP scope definition
  - Resource requirements and success criteria

- **[`data_model.md`](docs/data_model.md)** - Data Model Documentation
  - Entity relationships and data structure
  - Database schema definitions
  - Data validation rules

- **[`project_status.md`](docs/project_status.md)** - Project Status
  - Current development status
  - Progress tracking and milestones

- **[`technology_stack_selection.md`](docs/technology_stack_selection.md)** - Technology Stack Selection
  - Technology stack rationale and justification
  - Component specifications and versions
  - Architecture diagrams
  - Risk assessment and mitigation

### Additional Resources

- **`prompts/`** - Development prompts and guidance
- **`resources/`** - Additional project resources

## Project Structure

```text
E80_pm_mockup/
├── docs/                    # Project documentation
│   ├── prd.md              # Product Requirements Document
│   ├── plan.md             # Project plan and roadmap
│   ├── data_model.md       # Data model documentation
│   └── project_status.md   # Current project status
├── prompts/                 # Development prompts
├── resources/              # Project resources
└── README.md               # This file
```

## Key Features

The MVP will support:

- **Project Structure Management**: Create and manage projects, Work Breakdown Elements (WBEs), and cost elements
- **Budget & Revenue Management**: Allocate budgets and revenues, create time-phased plans
- **Cost Recording**: Register actual costs and track expenditures
- **Earned Value Tracking**: Record work completion and calculate EVM metrics
- **Forecasting**: Create and update estimates at completion (EAC)
- **Change Order Management**: Process scope changes and contract modifications
- **EVM Calculations**: Automatic calculation of CPI, SPI, variances, and performance indices
- **Reporting & Dashboards**: Generate standard EVM reports and performance visualizations

## Technology Stack

The MVP is built using modern, industry-standard technologies:

- **Backend**: FastAPI (Python) - High-performance async API framework
- **Frontend**: React 18+ with TypeScript - Modern, component-based UI
- **Database**: SQLite (MVP) / PostgreSQL (production) - Relational database with production migration path
- **ORM**: SQLAlchemy 2.0+ - Python SQL toolkit and ORM
- **Testing**: pytest (backend), Jest + React Testing Library (frontend)

See [`docs/technology_stack_selection.md`](docs/technology_stack_selection.md) for detailed technology rationale and architecture.

## Development Status

This project follows an agile development methodology with a planned 12-week MVP timeline organized into six two-week sprints. See [`docs/plan.md`](docs/plan.md) for detailed sprint breakdowns and [`docs/project_status.md`](docs/project_status.md) for current status.

## License

See [LICENSE](LICENSE) file for license information.
