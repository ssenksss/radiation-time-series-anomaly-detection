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

export type EvaluationMode = 'supervised' | 'unsupervised' | 'pending'
export type ModelCategory = 'unsupervised' | 'supervised' | 'future'

export interface ModelComparisonItem {
    id: string
    model: string
    category?: ModelCategory
    requiresLabels?: boolean
    enabled?: boolean
    disabledReason?: string | null
    score: number | null
    modelScore?: number | null
    accuracy: number | null
    precision: number | null
    recall: number | null
    fpr: number | null
    fnr: number | null
    evaluationMode?: EvaluationMode
    totalRecords?: number
    totalAnomalies?: number
    anomalyRate?: number | null
    active: boolean
    status: string
}

export interface AvailableModel {
    id: string
    name: string
    status: string
    category?: ModelCategory
    requiresLabels?: boolean
    enabled?: boolean
    disabledReason?: string | null
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

export interface ModelInfoGroups {
    unsupervised: string[]
    supervised: string[]
    future: string[]
}

export interface ModelInfo {
    currentModel: string
    activeModelId?: string
    accuracy: number | null
    precision: number | null
    recall?: number | null
    fpr: number | null
    fnr?: number | null
    modelScore?: number | null
    evaluationMode?: EvaluationMode
    datasetHasLabels?: boolean
    hasLabels?: boolean
    totalRecords?: number
    totalAnomalies?: number
    anomalyRate?: number | null
    source: string
    availableModels: AvailableModel[]
    selectedModels: SelectedModels
    confusionMatrix: ConfusionMatrix
    comparison: ModelComparisonItem[]
    groups?: ModelInfoGroups
    lastTrainedAt?: string
}

export interface PipelineStatus {
    jobId: string | null
    status: 'idle' | 'running' | 'success' | 'failed'
    message: string
    startedAt: string | null
    finishedAt: string | null
    activeDatasetId: number | null
    stdoutTail: string
    stderrTail: string
    errorMessage: string | null
}

export interface AppSettings {
    threshold: number
    activeModel: string
    activeDatasetId?: number
    pipeline?: PipelineStatus
}

export interface DatasetInfo {
    id: number
    name: string
    originalFilename: string
    sourceType: string
    uploadedAt: string
    rowCount: number
    status: string
    isActive: boolean
}

export interface DatasetUploadResponse {
    message: string
    filename: string
    savedPath: string
    success: boolean
    activeDatasetId: number
    pipelineOutput: string
}