# Label Mechanics

**The machinery behind independent labels.**

Label Mechanics is an early-stage SaaS project for small and independent record labels.

The project explores how labels can connect release management, costs, sales, and promotional activity in one place, with a particular focus on understanding the economics and results of individual releases.

## Current direction

The current experiment is built around a simple vertical slice:

**Release → Economics → Campaign → Result**

Rather than attempting to build a complete label management platform first, the goal is to test this workflow using real historical release data and determine which information is actually useful to independent labels.

The project deliberately avoids claiming marketing attribution where the available data cannot support it. The goal is to connect costs, promotional activity, timing, and measurable outcomes to provide useful context for future release decisions.

## Current features

The backend currently includes:

- multi-tenant label and membership system
- release and release format management
- track management
- contact management
- orders and order items
- stock tracking
- automatic stock updates when orders are paid
- financial transactions
- income and expense tracking
- release-level financial summaries
- transaction filtering
- marketing campaigns linked to releases
- tenant isolation across API resources

## Business logic

The API implements several domain and tenant-isolation rules:

- users can only access data belonging to labels they are members of
- releases, contacts, orders, and transactions are scoped to the current user's labels
- release formats and campaigns inherit tenant ownership through their release
- contacts assigned to orders must belong to the same label
- order items cannot reference release formats belonging to another label
- paid orders automatically reduce available stock
- paid orders automatically create sales income transactions
- repeated status changes do not create duplicate sales transactions
- order payment, stock updates, and transaction creation are handled as a single atomic operation

## Architecture

The backend is currently divided into three main Django applications:

```text
backend/
└── apps/
    ├── core/        # labels, memberships, releases, contacts and orders
    ├── economics/   # income, expenses and financial summaries
    └── campaigns/   # release marketing campaigns
```

`Label` acts as the tenant. Access to label data is managed through `Membership`, and API querysets and validation rules enforce tenant isolation.

## Tech stack

- Python
- Django
- Django REST Framework
- Docker

Frontend development has not started yet.

## Project status

Label Mechanics is currently an **experiment build / early MVP**.

The current focus is not feature completeness. The goal is to validate the core workflow on real independent-label data before expanding the product.

Current development is focused on connecting:

```text
Release
   ↓
Economics
   ↓
Campaign
   ↓
Result
```

The next stage is to connect campaign activity with release economics and then test the model using data from real historical releases.

## Local development

Clone the repository and create a virtual environment.

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-secret-key
```

Run migrations:

```bash
cd backend
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

## Security

Environment variables and local development data are excluded from version control.

Do not commit `.env` files, credentials, API keys, or production secrets.

## Roadmap

The immediate development priorities are:

- connect campaign activity with financial transactions
- strengthen cross-tenant validation
- add automated tests for tenant isolation and order payment logic
- validate the workflow using real historical release data
- define useful campaign result metrics based on real label workflows

## License

No license has been selected yet.