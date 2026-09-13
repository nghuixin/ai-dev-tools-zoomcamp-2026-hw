export class ApiError extends Error {
  detail: string
  status: number

  constructor(detail: string, status = 400) {
    super(detail)
    this.name = 'ApiError'
    this.detail = detail
    this.status = status
  }

  toJSON() {
    return { detail: this.detail }
  }
}
