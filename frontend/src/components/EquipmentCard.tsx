type EquipmentCardProps = {
  name: string
  assetTag: string
  status: string
}

function EquipmentCard({ name, assetTag, status }: EquipmentCardProps) {
  return (
    <article>
      <h2>{name}</h2>
      <p>Asset tag: {assetTag}</p>
      <p>Status: {status}</p>
    </article>
  )
}

export default EquipmentCard