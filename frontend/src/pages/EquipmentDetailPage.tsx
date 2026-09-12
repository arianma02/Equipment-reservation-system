import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

type Equipment = {
  id: number
  name: string
  asset_tag: string
  category_id: number
  category_name: string
  status: string
}

function EquipmentDetailPage() {
  const { id } = useParams()

  const [equipment, setEquipment] = useState<Equipment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadEquipment() {
      setLoading(true)
      setError('')
      setEquipment(null)

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/equipment/${id}`,
        )

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
  }, [id])

  if (loading) {
    return <p>Loading equipment...</p>
  }

  if (error || !equipment) {
    return <p>Failed to load equipment</p>
  }

  return (
    <section>
      <h2>{equipment.name}</h2>
      <p>Asset tag: {equipment.asset_tag}</p>
      <p>Category: {equipment.category_name}</p>
      <p>Status: {equipment.status}</p>
    </section>
  )
}

export default EquipmentDetailPage