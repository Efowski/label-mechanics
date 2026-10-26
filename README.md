# Label Mechanics

**The machinery behind independent labels.**

Label Mechanics is an early-stage SaaS project for small and independent record labels.

The project explores how labels can connect release management, costs, sales and promotional activity in one place, with a particular focus on understanding the economics and results of individual releases.

## Current direction

The current experiment is built around a simple vertical slice:

**Release → Economics → Campaign → Result**

Instead of attempting to build a complete label management platform first, the goal is to test this workflow using real historical release data and determine which information is actually useful to independent labels.

## Current features

The backend currently includes:

- multi-tenant label and membership system
- release and release format management
- track management
- contacts
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

Some of the current backend logic includes:

- users can only access data belonging to labels they are members of
- release formats and campaigns inherit tenant ownership through their release
- order items are validated against the order's label
- paid orders automatically reduce stock
- paid orders automatically create sales income transactions
- repeated status changes do not create duplicate sales transactions
- financial operations related to order payment are performed atomically

## Tech stack

- Python
- Django
- Django REST Framework
 
- Docker

Frontend development has not started yet.

## Project status

Label Mechanics is currently an **experiment build / early MVP**.

The current focus is not feature completeness. The goal is to validate the core workflow on real independent-label data before expanding the product.

The next stage connects campaign activity with release economics and measurable results.

## Local development

Create and activate a virtual environment, install dependencies:

```bash
pip install -r requirements.txt

Create a .env file in the project root:
DJANGO_SECRET_KEY=your-secret-key

Then run migrations:
cd backend
python manage.py migrate
python manage.py runserver

Security
Environment variables and local development data are excluded from version control.

Do not commit .env files or production credentials.
License
No license has been selected yet.