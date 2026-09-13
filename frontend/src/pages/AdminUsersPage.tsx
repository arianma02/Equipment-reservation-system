import { useEffect, useState } from "react";
import { API_URL } from "../config";
import type { User } from "../types";

function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updateError, setUpdateError] = useState("");

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
  }

  if (loading) {
    return <p>Loading users...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <main>
      <h2>Manage Users</h2>

      {users.map((user) => (
        <article key={user.id}>
          <p>Email: {user.email}</p>

          <label>
            Role:
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
            Status:
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
        </article>
      ))}
      {updateError && <p>{updateError}</p>}
    </main>
  );
}

export default AdminUsersPage;
