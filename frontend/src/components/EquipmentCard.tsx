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
      <h2>
        <Link to={`/equipment/${id}`}>{name}</Link>
      </h2>

      <p>Asset tag: {assetTag}</p>
      <p>Category: {categoryName}</p>
      <p>Status: {status}</p>
    </article>
  );
}

export default EquipmentCard;
