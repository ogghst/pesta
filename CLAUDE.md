# BackCast - Project Earned Value Simulator, Time Traveller and Analyzer

## Project Overview

BackCast is a comprehensive Project Budget Management and Earned Value Management (EVM) application designed for end-of-line automation projects. The system serves as a simulation and validation platform to model complex project scenarios with multiple Work Breakdown Elements (WBEs) and departmental cost elements, enabling organizations to test and validate financial management processes before implementing them in production environments.

The application provides a full EVM analytics platform that enables the Project Management Directorate to:
- Model complex project scenarios with multiple machines (WBEs) and departmental cost elements
- Track project financial performance using EVM principles
- Validate business rules and performance metrics under various conditions
- Support complete project lifecycle financial management including budgets, costs, forecasts, change orders, and quality events
- Generate accurate EVM calculations and reports for decision-making

## Technology Stack

- **Backend**: FastAPI with Python, SQLModel for ORM, PostgreSQL database
- **Frontend**: React with TypeScript, Vite, TanStack Query, TanStack Router, Chakra UI
- **Database**: PostgreSQL 17
- **Authentication**: JWT with secure password hashing
- **AI Features**: Langchain and Langgraph for AI-driven project assessment
- **WebSocket Support**: For AI chat functionality
- **Containerization**: Docker Compose with Traefik as reverse proxy
- **CI/CD**: GitHub Actions for deployment
- **Testing**: Pytest for backend, Playwright for frontend end-to-end tests

## Project Structure

```
/
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── models/       # SQLModel database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── crud/         # CRUD operations
│   │   ├── core/         # Core configurations
│   │   └── main.py       # Application entry point
│   ├── scripts/          # Utility scripts
│   └── pyproject.toml    # Python dependencies
├── frontend/             # React frontend application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── routes/       # Application routes
│   │   ├── client/       # Generated OpenAPI client
│   │   └── theme.tsx     # Chakra UI theme
│   └── package.json      # Node.js dependencies
├── docs/                 # Project documentation
│   ├── prd.md            # Product Requirements Document
│   ├── plan.md           # Project plan and roadmap
│   ├── data_model.md     # Data model documentation
│   └── project_status.md # Current project status
├── docker-compose.yml    # Docker Compose configuration
├── .env                  # Environment variables
└── README.md
```

## Core Architecture

### Data Model

The system uses a hierarchical project structure:
- **Project**: Top-level container with customer info, contract value, dates
- **WBE (Work Breakdown Element)**: Individual machines or deliverables within projects
- **Cost Element**: Department-level budgets and responsibilities within WBEs

Key entities include:
- Projects, WBEs, Cost Elements
- Cost Registrations (actual costs)
- Earned Value Entries (physical progress)
- Forecasts (EAC - Estimate at Completion)
- Baseline Logs (historical snapshots)
- Change Orders (scope modifications)
- Quality Events (defects and rework)

### API Endpoints

The backend provides comprehensive API endpoints across multiple domains:
- Authentication and user management
- Project, WBE, and Cost Element management
- Cost registrations and earned value tracking
- Forecast management
- EVM calculations and reporting
- Baseline management
- AI chat functionality for project analysis
- WebSocket support for real-time AI interactions

## Building and Running

### Development Setup

1. **Prerequisites**: Docker, Docker Compose, uv (Python package manager), Node.js

2. **Start the Development Stack**:
   ```bash
   docker compose watch
   ```

3. **Development URLs**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8010
   - Swagger UI: http://localhost:8010/docs
   - Adminer: http://localhost:6080

### Local Development

- **Backend**: Activate virtual environment with `uv sync && source .venv/bin/activate`
- **Frontend**: Install dependencies with `npm install` and run with `npm run dev`
- The Docker Compose setup allows turning off services and using local development servers while maintaining the same ports

### Environment Configuration

The system uses multiple `.env` files for configuration:
- `.env`: Development configuration
- `.env.production`: Production configuration

Key environment variables include:
- Database credentials and configuration
- API keys and secrets
- SMTP settings for email
- AI-related configuration (FERNET_KEY for OpenAI API key encryption)

## Development Conventions

### Backend (Python)
- FastAPI framework with proper dependency injection
- SQLModel for database interactions
- Pydantic for data validation
- Alembic for database migrations
- MyPy for type checking
- Ruff for linting and formatting
- Comprehensive testing with Pytest

### Frontend (React/TypeScript)
- TypeScript for type safety
- Vite for fast development
- TanStack Query for data fetching and caching
- TanStack Router for routing
- Chakra UI for component library
- React Hook Form for form handling
- Chart.js for data visualization

### Code Quality
- Pre-commit hooks enforce code formatting and linting
- Comprehensive test coverage
- Type checking
- Consistent styling with established tools

## Key Features

### EVM Capabilities
- Complete EVM calculations (PV, EV, AC, CPI, SPI, TCPI, etc.)
- Baseline management with historical snapshots
- Variance analysis (CV, SV, VAC)
- Forecasting with multiple methods
- Performance trending and reporting

### AI Integration
- AI-driven project assessment
- WebSocket-based chat interface for data analysis
- OpenAI integration with encrypted API key storage
- Langchain/Langgraph for complex AI workflows

### Time Machine Feature
- Historical data viewing at specific control dates
- Ability to see project status at any point in time
- Baseline comparison capabilities

### Reporting and Analytics
- Standard EVM reports
- Trend analysis dashboards
- Custom reporting capabilities
- Quality cost analysis

## Testing

### Backend Tests
Run with:
```bash
bash ./scripts/test.sh
```

### Frontend Tests
Run end-to-end tests with:
```bash
npx playwright test
```

### Test Coverage
- Backend: Pytest with coverage reports
- Frontend: Playwright for E2E testing
- CI/CD integration for automated testing

## Deployment

### Production Deployment
- Docker Compose with Traefik reverse proxy
- Automatic HTTPS certificate management
- WebSocket support for AI features
- Multiple environment support (staging, production)

### CI/CD
- GitHub Actions for continuous integration/deployment
- Automated testing and security checks
- Multiple deployment environments

## Security

- JWT-based authentication
- Secure password hashing
- API key encryption with Fernet
- CORS configuration
- Input validation and sanitization

## AI Chat WebSocket Support

The system includes WebSocket support for AI chat functionality:
- WebSocket endpoints under `/api/v1/ai-chat`
- Traefik configuration for WebSocket proxying
- Fallback Apache configuration available for non-Traefik setups

## Configuration and Customization

- Extensive `.env` configuration options
- Multiple deployment environments support
- Customizable EVM calculation parameters
- Configurable user roles and permissions
