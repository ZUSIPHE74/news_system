# News System

A Django web application for publishing news with role-based workflows, featuring a premium UI and robust role management.

---

### CRITICAL: PUBLISHER & JOURNALIST ASSOCIATION WORKFLOW

If you are wondering **how Publishers are stored**, **where to view them**, or **why they don't immediately appear in the journalist's article submission dropdown**, here is how the system's secure brand-control design works:

1. **How Publishers are Stored**: When an **Editor** clicks **Create Publisher** (accessible from the top navbar or Editor Dashboard), the publisher is stored securely in the database.
2. **Where Editors can View Publishers**: We have added a direct **"View Publishers"** link right in the top navigation bar for all logged-in Editors (and inside the Editor Dashboard). Here, you can see all registered publishers and their creation dates.
3. **Why Journalists can't arbitrary select any Publisher when submitting articles**: 
   In a realistic, secure publishing platform, journalists are contracted with a specific publishing house—they cannot post under any publisher they want. Therefore, a Journalist is linked to **one publisher** via their profile settings.
4. **How a Journalist publishes under a newly created Publisher**:
   - The **Journalist** must log in, click **Edit Profile** in the top navigation bar.
   - Go to the **Publisher Association** search field (which has an autocomplete datalist populated with all active publishers stored in the database).
   - Start typing the name of the newly created publisher, select it, and click **Save Changes**.
   - Now, when the Journalist clicks **Submit Article**, they will see the option to **"Post As: Publisher-Branded"**. Choosing this automatically links their article to that publisher!

---

## Current Features

- **Authentication**:
  - Role-based registration: Users can select their role (**Reader**, **Journalist**, or **Editor**) during sign-up.
  - Enforced unique email addresses for all accounts.
  - Smooth login flow with smart redirection to intended destinations.
- **Role-based Experience**:
  - `reader`: Browse approved articles, follow publishers/journalists, and manage a personalized profile.
  - `journalist`: Create, view, update, and delete their own articles and newsletters.
  - `editor`: Approve, update, and delete articles, manage publishers, and create, view, update, and delete newsletters.
- **Article Workflow**:
  - Statuses: `Draft`, `Pending Review`, `Approved`, `Rejected`.
  - Automatic publisher branding on approval.
- **Newsletter Management**:
  - Full CRUD functionality: Newsletters can be created, viewed, updated, and deleted by authorized journalists (authors) and editors (publisher-scoped).
- **Publisher Management**:
  - Organizational profiles (e.g., **Jane Publisher**) with dedicated editing interfaces for editors.
  - **Publisher Workflow**: Editors create new publishers via the "Create Publisher" button and can view all active publishers on the "View Publishers" page.
  - **Journalist Association**: Once an Editor creates a publisher, journalists must first associate themselves with it on their Profile page. After doing so, they can choose to submit articles as "Publisher-Branded" for their chosen publisher.
- **REST API**:
  - `GET /api/articles/` returns a personalized feed based on user subscriptions.
  - Shared article logging for external integrations.

## Project Structure

```text
news_system/
|-- manage.py
|-- requirements.txt
|-- .env.example
|-- news_app/
|   |-- models.py
|   |-- views.py
|   |-- templates/
|   |   `-- news_app/   <-- Consolidated templates
|   |-- ...
`-- news_project/
    |-- settings.py
    `-- ...
```

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-link>
cd news_system
```

### 2. Create Virtual Environment
**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```
**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup (MariaDB/MySQL)
Ensure your MariaDB server is running. Create the project database:
```sql
-- Login to MariaDB
mysql -u root -p

-- Run the following query
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 5. Environment Configuration
Copy the template and adjust your database credentials:
```bash
cp .env.example .env
```
Update `.env` with your `DB_USER` and `DB_PASSWORD`.

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Start the Application
```bash
python manage.py runserver
```

## Usage

1. Open `http://127.0.0.1:8000/` in your browser.
2. Use **Sign Up** to create an account.
3. Access role-specific dashboards:
   - **Editor**: Manage articles, publishers, and create/manage newsletters.
   - **Journalist**: Submit/manage articles and create/manage newsletters.
   - **Reader**: View news and manage subscriptions.

### Publisher Organizational Workflow

The News System features a robust, role-based organizational model to secure brand integrity and manage publisher-journalist collaborations:

1. **Publisher Registration**: An **Editor** creates a new Publisher profile via the **Create Publisher** button on the platform. The publisher is securely created and registered in the database.
2. **Journalist-Publisher Association**: To protect publishers from unauthorized posting, journalists are not linked to publishers by default. A **Journalist** must navigate to their profile, select **Edit Profile**, choose the newly registered Publisher from the autocomplete/list, and save.
3. **Publisher-Branded Content Submission**: Once associated, the Journalist can submit articles and mark them as **Publisher-Branded**. The article will be associated with their publisher for review.
4. **Approval & Branding**: When an **Editor** approves the pending article, it is automatically published with full publisher branding, and notifications are sent out to all subscribed readers of both the author and the publisher.

## Documentation

- Full documentation of classes and methods is provided via Python docstrings throughout the codebase.

## Submission Notes

- **Included**: All source code, updated `README.md`, `requirements.txt`, `.env.example`, and migrations.
- **Enhanced Feature Set**: This version includes the full profile management system, rebranded publisher identity, and advanced journalist-publisher association tools.
- **Clean Submission**: Excluded `.venv`, `__pycache__`, and local environment files for a professional package.
- **Evaluation Tip**: Use the `editor_demo` and `journalist_demo` accounts (Password: `DemoPass123!`) to instantly explore the organizational workflows.
