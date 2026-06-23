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
    id: string
    model: string
    score: number
    accuracy: number | null
    precision: number | null
    recall: number | null
    fpr: number | null
    fnr: number | null
    active: boolean
    status: string
}

export interface AvailableModel {
    id: string
    name: string
    status: string
}

export interface SelectedModels {
    modelA: string
    modelB: string
}

export interface ConfusionMatrix {
    tp: number
    tn: number
    fp: number
    fn: number
}

export interface ModelInfo {
    currentModel: string
    accuracy: number
    precision: number
    fpr: number
    fnr: number
    source: string
    availableModels: AvailableModel[]
    selectedModels: SelectedModels
    confusionMatrix: ConfusionMatrix
    comparison: ModelComparisonItem[]
}

export interface AppSettings {
    threshold: number
    activeModel: string
}