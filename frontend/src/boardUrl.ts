export function readBoardIdFromLocation(location: { search: string }): string | null {
  const value = new URLSearchParams(location.search).get('board')
  return value && value.length > 0 ? value : null
}

export function syncBoardIdInLocation(
  location: Location,
  history: History,
  boardId: string | null,
) {
  const url = new URL(location.href)
  if (boardId) url.searchParams.set('board', boardId)
  else url.searchParams.delete('board')
  const next = `${url.pathname}${url.search}${url.hash}`
  const current = `${location.pathname}${location.search}${location.hash}`
  if (next !== current) history.replaceState(null, '', next)
}
