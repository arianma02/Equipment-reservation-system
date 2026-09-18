import { useEffect, useState } from "react";
import { API_URL } from "../config";
import type { Category, Equipment } from "../types";

function AdminEquipmentPage() {
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [assetTag, setAssetTag] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [createError, setCreateError] = useState("");
  const [creating, setCreating] = useState(false);

  const [categories, setCategories] = useState<Category[]>([]);
  const [updateError, setUpdateError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editAssetTag, setEditAssetTag] = useState("");
  const [editCategoryId, setEditCategoryId] = useState("");

  useEffect(() => {
    async function loadEquipment() {
      try {
        const response = await fetch(`${API_URL}/equipment`);

        if (!response.ok) {
          throw new Error("Failed to load equipment");
        }

        const data = await response.json();
        setEquipment(data);
      } catch {
        setError("Failed to load equipment");
      } finally {
        setLoading(false);
      }
    }

    loadEquipment();
  }, []);

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
        setCreateError("Failed to load categories");
      }
    }

    loadCategories();
  }, []);

  async function createEquipment(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      setCreateError("You must be logged in");
      return;
    }

    setCreateError("");
    setCreating(true);

    try {
      const response = await fetch(`${API_URL}/equipment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          asset_tag: assetTag,
          category_id: Number(categoryId),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to create equipment");
      }

      setEquipment((previousEquipment) => [...previousEquipment, data]);

      setName("");
      setAssetTag("");
      setCategoryId("");
    } catch (error) {
      if (error instanceof Error) {
        setCreateError(error.message);
      } else {
        setCreateError("Failed to create equipment");
      }
    } finally {
      setCreating(false);
    }
  }

  async function updateEquipment(
    equipmentId: number,
    updates: {
      name?: string;
      asset_tag?: string;
      category_id?: number;
      status?: string;
    },
  ): Promise<boolean> {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setUpdateError("You must be logged in");
      return false;
    }

    setUpdateError("");

    try {
      const response = await fetch(`${API_URL}/equipment/${equipmentId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to update equipment");
      }

      setEquipment((previousEquipment) => {
        const newEquipment = previousEquipment.map((item) => {
          if (item.id === equipmentId) {
            return { ...item, ...data };
          }

          return item;
        });

        return newEquipment;
      });

      return true;
    } catch (error) {
      if (error instanceof Error) {
        setUpdateError(error.message);
      } else {
        setUpdateError("Failed to update equipment");
      }

      return false;
    }
  }

  function startEditing(item: Equipment) {
    setEditingId(item.id);
    setEditName(item.name);
    setEditAssetTag(item.asset_tag);
    setEditCategoryId(String(item.category_id));
  }

  async function saveEquipment(
    event: React.FormEvent<HTMLFormElement>,
    equipmentId: number,
  ) {
    event.preventDefault();

    const success = await updateEquipment(equipmentId, {
      name: editName,
      asset_tag: editAssetTag,
      category_id: Number(editCategoryId),
    });

    if (success) {
      setEditingId(null);
    }
  }
  if (loading) {
    return (
      <main>
        <div className="page-state">Loading equipment...</div>
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
        <h2>Manage equipment</h2>
        <p className="page-description">
          Add equipment and manage existing items, categories, and status.
        </p>
      </section>

      <section className="admin-form-card">
        <div className="admin-form-heading">
          <p className="admin-card-label">CREATE</p>
          <h3>Add equipment</h3>
        </div>

        <form className="admin-create-form" onSubmit={createEquipment}>
          <label>
            Name
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>

          <label>
            Asset tag
            <input
              type="text"
              value={assetTag}
              onChange={(event) => setAssetTag(event.target.value)}
              required
            />
          </label>

          <label>
            Category
            <select
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
              required
            >
              <option value="">Select a category</option>

              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          <button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Add equipment"}
          </button>
        </form>

        {createError && <p className="error-message">{createError}</p>}
      </section>

      <div className="admin-item-list">
        {equipment.map((item) => (
          <article className="admin-item-card" key={item.id}>
            <div className="admin-item-heading">
              <div>
                <p className="admin-card-label">EQUIPMENT</p>
                <h3>{item.name}</h3>
              </div>

              <span className={`status-badge status-${item.status}`}>
                {item.status}
              </span>
            </div>

            {editingId === item.id ? (
              <form
                className="admin-edit-form"
                onSubmit={(event) => saveEquipment(event, item.id)}
              >
                <div className="form-row">
                  <label>
                    Name
                    <input
                      type="text"
                      value={editName}
                      onChange={(event) => setEditName(event.target.value)}
                      required
                    />
                  </label>

                  <label>
                    Asset tag
                    <input
                      type="text"
                      value={editAssetTag}
                      onChange={(event) => setEditAssetTag(event.target.value)}
                      required
                    />
                  </label>

                  <label>
                    Category
                    <select
                      value={editCategoryId}
                      onChange={(event) =>
                        setEditCategoryId(event.target.value)
                      }
                      required
                    >
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

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
              <div className="admin-equipment-meta">
                <div>
                  <span>Asset tag</span>
                  <strong>{item.asset_tag}</strong>
                </div>

                <div>
                  <span>Category</span>
                  <strong>{item.category_name}</strong>
                </div>
              </div>
            )}

            {editingId !== item.id && (
              <div className="admin-item-actions">
                <button onClick={() => startEditing(item)}>Edit</button>

                <label className="admin-status-control">
                  Status
                  <select
                    value={item.status}
                    onChange={(event) =>
                      updateEquipment(item.id, { status: event.target.value })
                    }
                  >
                    <option value="active">Active</option>
                    <option value="maintenance">Maintenance</option>
                    <option value="retired">Retired</option>
                  </select>
                </label>
              </div>
            )}
          </article>
        ))}
      </div>

      {updateError && <p className="error-message">{updateError}</p>}
    </main>
  );
}

export default AdminEquipmentPage;
