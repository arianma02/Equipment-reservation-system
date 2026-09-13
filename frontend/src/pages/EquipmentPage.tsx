import { useEffect, useState } from "react";
import EquipmentCard from "../components/EquipmentCard";
import type { Equipment, Category } from "../types";
import { API_URL } from "../config";

function EquipmentPage() {
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);

  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [categoryError, setCategoryError] = useState("");

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
        setCategoryError("Failed to load categories");
      }
    }

    loadCategories();
  }, []);

  useEffect(() => {
    async function loadEquipment() {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams();

        if (statusFilter) {
          params.append("status", statusFilter);
        }

        if (categoryFilter) {
          params.append("category_id", categoryFilter);
        }

        const queryString = params.toString();

        const url = queryString
          ? `${API_URL}/equipment?${queryString}`
          : `${API_URL}/equipment`;

        const response = await fetch(url);

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
  }, [statusFilter, categoryFilter]);

  return (
    <main>
      <h2>Equipment</h2>

      <div className="form-row">
        <label>
          Status:
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="maintenance">Maintenance</option>
            <option value="retired">Retired</option>
          </select>
        </label>

        <label>
          Category:
          <select
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value)}
          >
            <option value="">All</option>

            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {categoryError && <p>{categoryError}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p>{error}</p>
      ) : equipment.length === 0 ? (
        <p className="empty-message">
          No equipment matches the selected filters.
        </p>
      ) : (
        <div className="equipment-grid">
          {equipment.map((item) => (
            <EquipmentCard
              key={item.id}
              id={item.id}
              name={item.name}
              assetTag={item.asset_tag}
              categoryName={item.category_name}
              status={item.status}
            />
          ))}
        </div>
      )}
    </main>
  );
}

export default EquipmentPage;
