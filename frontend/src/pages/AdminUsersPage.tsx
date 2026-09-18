import { useEffect, useState } from "react";
import { API_URL } from "../config";
import type { User } from "../types";
import { useAuth } from "../hooks/useAuth";

function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updateError, setUpdateError] = useState("");

  const { user: currentUser, refreshUser } = useAuth();

  useEffect(() => {
    async function loadUsers() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("You must be logged in");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/users`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Failed to load users");
        }

        setUsers(data);
      } catch (error) {
        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError("Failed to load users");
        }
      } finally {
        setLoading(false);
      }
    }

    loadUsers();
  }, []);

  async function updateUser(
    userId: number,
    updates: { role?: string; status?: string },
  ) {
    const token = localStorage.getItem("access_token");
    setUpdateError("");

    if (!token) {
      setUpdateError("You must be logged in");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/users/${userId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to update user");
      }

      setUsers((previousUsers) => {
        const newUsers = previousUsers.map((user) => {
          if (user.id === userId) {
            return { ...user, ...data };
          }

          return user;
        });

        return newUsers;
      });
    } catch (error) {
      if (error instanceof Error) {
        setUpdateError(error.message);
      } else {
        setUpdateError("Failed to update user");
      }
    }
    if (currentUser?.id === userId) {
      await refreshUser();
    }
  }

  if (loading) {
    return (
      <main>
        <div className="page-state">Loading users...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <div className="page-state error-state">{error}</div>
      </main>
    );
  }

  return (
    <main>
      <section className="page-heading">
        <p className="eyebrow">ADMINISTRATION</p>
        <h2>Manage users</h2>
        <p className="page-description">
          View user accounts and manage their roles and status.
        </p>
      </section>

      <div className="admin-item-list">
        {users.map((user) => (
          <article className="admin-item-card user-admin-card" key={user.id}>
            <div className="admin-item-heading">
              <div>
                <p className="admin-card-label">USER</p>
                <h3>{user.email}</h3>
              </div>

              <span className={`status-badge status-${user.status}`}>
                {user.status}
              </span>
            </div>

            <div className="admin-user-controls">
              <label>
                Role
                <select
                  value={user.role}
                  onChange={(event) =>
                    updateUser(user.id, { role: event.target.value })
                  }
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </label>

              <label>
                Status
                <select
                  value={user.status}
                  onChange={(event) =>
                    updateUser(user.id, { status: event.target.value })
                  }
                >
                  <option value="active">Active</option>
                  <option value="disabled">Disabled</option>
                </select>
              </label>
            </div>
          </article>
        ))}
      </div>

      {updateError && <p className="error-message">{updateError}</p>}
    </main>
  );
}

export default AdminUsersPage;
