export interface Measurement {
    timestamp: string
    radiationLevel: number
    sensorId: string
    location: string
    temperature: number | null
    humidity: number | null
    isAnomaly: boolean
    anomalyScore: number
    anomalyType: string
    status: string
}

export interface Summary {
    datasetName: string
    totalMeasurements: number
    totalAnomalies: number
    currentLevel: number
    averageLevel: number
    maxLevel: number
    minLevel: number
    threshold: number
    activeAlert: boolean
    lastUpdated: string
}

export interface ModelComparisonItem {
    model: string
    score: number
}

export interface ModelInfo {
    currentModel: string
    accuracy: number
    precision: number
    fpr: number
    fnr: number
    source: string
    comparison: ModelComparisonItem[]
}