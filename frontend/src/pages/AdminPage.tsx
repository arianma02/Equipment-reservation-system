import { Link } from "react-router-dom";

function AdminPage() {
  return (
    <main>
      <section className="page-heading">
        <p className="eyebrow">ADMINISTRATION</p>
        <h2>Admin dashboard</h2>
        <p className="page-description">
          Manage users, equipment, categories, and reservations.
        </p>
      </section>

      <nav className="admin-grid">
        <Link to="/admin/users" className="admin-card">
          <div>
            <p className="admin-card-label">USERS</p>
            <h3>Manage users</h3>
            <p>View users and manage their account status and roles.</p>
          </div>

          <span className="admin-card-link">Open →</span>
        </Link>

        <Link to="/admin/equipment" className="admin-card">
          <div>
            <p className="admin-card-label">EQUIPMENT</p>
            <h3>Manage equipment</h3>
            <p>Add, edit, and manage reservable equipment.</p>
          </div>

          <span className="admin-card-link">Open →</span>
        </Link>

        <Link to="/admin/categories" className="admin-card">
          <div>
            <p className="admin-card-label">CATEGORIES</p>
            <h3>Manage categories</h3>
            <p>Create and update equipment categories.</p>
          </div>

          <span className="admin-card-link">Open →</span>
        </Link>

        <Link to="/admin/reservations" className="admin-card">
          <div>
            <p className="admin-card-label">RESERVATIONS</p>
            <h3>Manage reservations</h3>
            <p>Review reservations and their current status.</p>
          </div>

          <span className="admin-card-link">Open →</span>
        </Link>
      </nav>
    </main>
  );
}

export default AdminPage;
