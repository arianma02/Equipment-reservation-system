import { Link } from "react-router-dom";

type EquipmentCardProps = {
  id: number;
  name: string;
  assetTag: string;
  categoryName: string;
  status: string;
};

function EquipmentCard({
  id,
  name,
  assetTag,
  categoryName,
  status,
}: EquipmentCardProps) {
  return (
    <article className="equipment-card">
      <div className="equipment-card-header">
        <div>
          <p className="equipment-category">{categoryName}</p>
          <h2>{name}</h2>
        </div>

        <span className={`status-badge status-${status}`}>{status}</span>
      </div>

      <div className="equipment-meta">
        <span>Asset tag</span>
        <strong>{assetTag}</strong>
      </div>

      <Link className="equipment-link" to={`/equipment/${id}`}>
        View equipment →
      </Link>
    </article>
  );
}

export default EquipmentCard;
