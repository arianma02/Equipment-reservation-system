import { useEffect, useState } from 'react'
import EquipmentCard from '../components/EquipmentCard'

type Equipment = {
  id: number
  name: string
  asset_tag: string
  status: string
}

function EquipmentPage() {
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadEquipment() {
      try {
        const response = await fetch('http://127.0.0.1:8000/equipment')

        if (!response.ok) {
          throw new Error('Failed to load equipment')
        }

        const data = await response.json()
        setEquipment(data)
      } catch {
        setError('Failed to load equipment')
      } finally {
        setLoading(false)
      }
    }

    loadEquipment()
  }, [])

  if (loading) {
    return <p>Loading equipment...</p>
  }

  if (error) {
    return <p>{error}</p>
  }

  return (
    <section>
      <h2>Equipment</h2>

      {equipment.length === 0 && <p>No equipment found.</p>}

      {equipment.map((item) => (
        <EquipmentCard
          key={item.id}
          name={item.name}
          assetTag={item.asset_tag}
          status={item.status}
        />
      ))}
    </section>
  )
}

export default EquipmentPage