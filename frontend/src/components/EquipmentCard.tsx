type EquipmentCardProps = {
  name: string;
  assetTag: string;
  categoryName: string;
  status: string;
};

function EquipmentCard({
  name,
  assetTag,
  categoryName,
  status,
}: EquipmentCardProps) {
  return (
    <article>
      <h2>{name}</h2>
      <p>Asset tag: {assetTag}</p>
      <p>Category: {categoryName}</p>
      <p>Status: {status}</p>
    </article>
  );
}

export default EquipmentCard;
