import { useEffect, useState } from 'react'
import EquipmentCard from '../components/EquipmentCard'

type Equipment = {
  id: number
  name: string
  asset_tag: string
  category_id: number
  category_name: string
  status: string
}

type Category = {
  id: number
  name: string
}

function EquipmentPage() {
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [categories, setCategories] = useState<Category[]>([])

  const [statusFilter, setStatusFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadCategories() {
      const response = await fetch('http://127.0.0.1:8000/categories')
      const data = await response.json()

      setCategories(data)
    }

    loadCategories()
  }, [])

  useEffect(() => {
    async function loadEquipment() {
      setLoading(true)
      setError('')

      try {
        const params = new URLSearchParams()

        if (statusFilter) {
          params.append('status', statusFilter)
        }

        if (categoryFilter) {
          params.append('category_id', categoryFilter)
        }

        const queryString = params.toString()

        const url = queryString
          ? `http://127.0.0.1:8000/equipment?${queryString}`
          : 'http://127.0.0.1:8000/equipment'

        const response = await fetch(url)

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
  }, [statusFilter, categoryFilter])

  if (loading) {
    return <p>Loading equipment...</p>
  }

  if (error) {
    return <p>{error}</p>
  }

  return (
    <section>
      <h2>Equipment</h2>

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

      {equipment.length === 0 && <p>No equipment found.</p>}

      {equipment.map((item) => (
        <EquipmentCard
          key={item.id}
          name={item.name}
          assetTag={item.asset_tag}
          categoryName={item.category_name}
          status={item.status}
        />
      ))}
    </section>
  )
}

export default EquipmentPage