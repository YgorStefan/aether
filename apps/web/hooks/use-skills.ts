'use client'

import { useEffect, useState } from 'react'
import { getSkills, type SkillMetadata } from '@/lib/api'

export function useSkills() {
  const [skills, setSkills] = useState<SkillMetadata[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSkills()
      .then(setSkills)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return { skills, loading, error }
}
