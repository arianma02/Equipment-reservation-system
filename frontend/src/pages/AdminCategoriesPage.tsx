import { useEffect, useState } from "react";
import { API_URL } from "../config";
import type { Category } from "../types";

function AdminCategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [createError, setCreateError] = useState("");
  const [creating, setCreating] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [updateError, setUpdateError] = useState("");

  const [deleteError, setDeleteError] = useState("");
  useEffect(() => {
    async function loadCategories() {
      try {
        const response = await fetch(`${API_URL}/categories`);

        if (!response.ok) {
          throw new Error("Failed to load categories");
        }

        const data = await response.json();
        setCategories(data);
      } catch {
        setError("Failed to load categories");
      } finally {
        setLoading(false);
      }
    }

    loadCategories();
  }, []);

  async function createCategory(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      setCreateError("You must be logged in");
      return;
    }

    setCreateError("");
    setCreating(true);

    try {
      const response = await fetch(`${API_URL}/categories`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to create category");
      }

      setCategories((previousCategories) => [...previousCategories, data]);

      setName("");
    } catch (error) {
      if (error instanceof Error) {
        setCreateError(error.message);
      } else {
        setCreateError("Failed to create category");
      }
    } finally {
      setCreating(false);
    }
  }

  function startEditing(category: Category) {
    setEditingId(category.id);
    setEditName(category.name);
  }

  async function updateCategory(
    event: React.FormEvent<HTMLFormElement>,
    categoryId: number,
  ) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      setUpdateError("You must be logged in");
      return;
    }

    setUpdateError("");

    try {
      const response = await fetch(`${API_URL}/categories/${categoryId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: editName,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to update category");
      }

      setCategories((previousCategories) =>
        previousCategories.map((category) =>
          category.id === categoryId ? data : category,
        ),
      );

      setEditingId(null);
    } catch (error) {
      if (error instanceof Error) {
        setUpdateError(error.message);
      } else {
        setUpdateError("Failed to update category");
      }
    }
  }

  async function deleteCategory(categoryId: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this category?",
    );

    if (!confirmed) {
      return;
    }

    const token = localStorage.getItem("access_token");

    if (!token) {
      setDeleteError("You must be logged in");
      return;
    }

    setDeleteError("");

    try {
      const response = await fetch(`${API_URL}/categories/${categoryId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to delete category");
      }

      setCategories((previousCategories) =>
        previousCategories.filter((category) => category.id !== categoryId),
      );
    } catch (error) {
      if (error instanceof Error) {
        setDeleteError(error.message);
      } else {
        setDeleteError("Failed to delete category");
      }
    }
  }
  if (loading) {
    return (
      <main>
        <p>Loading categories...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <p>{error}</p>
      </main>
    );
  }

  return (
    <main>
      <h2>Manage Categories</h2>

      <section className="admin-form-card">
        <h3>Add Category</h3>

        <form className="form-row" onSubmit={createCategory}>
          <label>
            Name:
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>

          <button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Add Category"}
          </button>
        </form>

        {createError && <p>{createError}</p>}
      </section>

      <div className="admin-item-list">
        {categories.map((category) => (
          <article className="admin-item-card" key={category.id}>
            {editingId === category.id ? (
              <form
                className="admin-edit-form"
                onSubmit={(event) => updateCategory(event, category.id)}
              >
                <label>
                  Name:
                  <input
                    type="text"
                    value={editName}
                    onChange={(event) => setEditName(event.target.value)}
                    required
                  />
                </label>

                <div className="button-row">
                  <button type="submit">Save</button>

                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => setEditingId(null)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <>
                <p className="admin-item-title">{category.name}</p>

                <div className="button-row">
                  <button onClick={() => startEditing(category)}>Edit</button>

                  <button
                    className="danger-button"
                    onClick={() => deleteCategory(category.id)}
                  >
                    Delete
                  </button>
                </div>
              </>
            )}
          </article>
        ))}
      </div>

      {deleteError && <p>{deleteError}</p>}
      {updateError && <p>{updateError}</p>}
    </main>
  );
}

export default AdminCategoriesPage;
