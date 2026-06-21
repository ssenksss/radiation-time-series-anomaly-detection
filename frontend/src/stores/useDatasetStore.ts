import { reactive } from 'vue'

type DatasetRecord = Record<string, string | number>

export interface ParsedDatasetRow {
    label: string
    value: number
    record: DatasetRecord
}

interface DatasetState {
    name: string
    source: string
    uploadedAt: string
    headers: string[]
    rows: ParsedDatasetRow[]
    isLoaded: boolean
    threshold: number
}

const STORAGE_KEY = 'radiation-monitoring-dataset'

const datasetState = reactive<DatasetState>({
    name: 'radiation_data.csv',
    source: 'Mock dataset',
    uploadedAt: '',
    headers: [],
    rows: [],
    isLoaded: false,
    threshold: 0.5,
})

function splitCsvLine(line: string): string[] {
    const result: string[] = []
    let current = ''
    let insideQuotes = false

    for (let i = 0; i < line.length; i += 1) {
        const char = line[i]

        if (char === '"') {
            if (insideQuotes && line[i + 1] === '"') {
                current += '"'
                i += 1
            } else {
                insideQuotes = !insideQuotes
            }
        } else if (char === ',' && !insideQuotes) {
            result.push(current.trim())
            current = ''
        } else {
            current += char
        }
    }

    result.push(current.trim())
    return result
}

function normalizeHeader(header: string): string {
    return header.trim().toLowerCase().replace(/\s+/g, '_')
}

function parseNumericValue(value: string): number {
    const cleaned = value
        .replace(',', '.')
        .replace(/[^\d.-]/g, '')
        .trim()

    const parsed = Number.parseFloat(cleaned)
    return Number.isFinite(parsed) ? parsed : 0
}

function detectTimestampIndex(headers: string[]): number {
    const normalized = headers.map(normalizeHeader)

    const candidates = [
        'timestamp',
        'date',
        'time',
        'datetime',
        'measured_at',
    ]

    const found = normalized.findIndex((header) => candidates.includes(header))
    return found >= 0 ? found : 0
}

function detectValueIndex(headers: string[]): number {
    const normalized = headers.map(normalizeHeader)

    const candidates = [
        'radiation_level',
        'radiation',
        'value',
        'level',
        'dose',
        'dose_rate',
        'usv_h',
        'µsv_h',
        'measurement',
    ]

    const found = normalized.findIndex((header) => candidates.includes(header))
    return found >= 0 ? found : Math.min(1, Math.max(headers.length - 1, 0))
}

function saveToStorage() {
    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
            name: datasetState.name,
            source: datasetState.source,
            uploadedAt: datasetState.uploadedAt,
            headers: datasetState.headers,
            rows: datasetState.rows,
            isLoaded: datasetState.isLoaded,
            threshold: datasetState.threshold,
        }),
    )
}

function loadFromStorage() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return

    try {
        const parsed = JSON.parse(raw)

        datasetState.name = parsed.name ?? datasetState.name
        datasetState.source = parsed.source ?? datasetState.source
        datasetState.uploadedAt = parsed.uploadedAt ?? ''
        datasetState.headers = parsed.headers ?? []
        datasetState.rows = parsed.rows ?? []
        datasetState.isLoaded = parsed.isLoaded ?? false
        datasetState.threshold = parsed.threshold ?? 0.5
    } catch (error) {
        console.error('Failed to restore dataset from storage:', error)
    }
}

function parseCsvText(text: string): { headers: string[]; rows: ParsedDatasetRow[] } {
    const lines = text
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0)

    if (lines.length < 2) {
        throw new Error('CSV file must contain a header row and at least one data row.')
    }

    const headers = splitCsvLine(lines[0])
    const timestampIndex = detectTimestampIndex(headers)
    const valueIndex = detectValueIndex(headers)

    const rows = lines.slice(1).map((line, index) => {
        const cols = splitCsvLine(line)

        const record: DatasetRecord = {}
        headers.forEach((header, headerIndex) => {
            record[header] = cols[headerIndex] ?? ''
        })

        const label = cols[timestampIndex] || `Row ${index + 1}`
        const value = parseNumericValue(cols[valueIndex] ?? '0')

        return {
            label,
            value,
            record,
        }
    })

    return { headers, rows }
}

async function uploadCsv(file: File) {
    const text = await file.text()
    const parsed = parseCsvText(text)

    datasetState.name = file.name
    datasetState.source = 'Uploaded CSV'
    datasetState.uploadedAt = new Date().toLocaleString()
    datasetState.headers = parsed.headers
    datasetState.rows = parsed.rows
    datasetState.isLoaded = true

    saveToStorage()
}

function resetDataset() {
    datasetState.name = 'radiation_data.csv'
    datasetState.source = 'Mock dataset'
    datasetState.uploadedAt = ''
    datasetState.headers = []
    datasetState.rows = []
    datasetState.isLoaded = false
    datasetState.threshold = 0.5

    saveToStorage()
}

loadFromStorage()

export function useDatasetStore() {
    return {
        datasetState,
        uploadCsv,
        resetDataset,
    }
}