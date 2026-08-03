/** Скачивает массив объектов как CSV (UTF-8 с BOM для Excel). */
export function exportCsv(filename: string, rows: Record<string, string | number | null | undefined>[]) {
  if (!rows.length) return
  const headers = Object.keys(rows[0])
  const esc = (v: string | number | null | undefined) => {
    const s = v === null || v === undefined ? '' : String(v)
    return `"${s.replace(/"/g, '""')}"`
  }
  const lines = [headers.join(';'), ...rows.map((r) => headers.map((h) => esc(r[h])).join(';'))]
  const blob = new Blob([`\uFEFF${lines.join('\r\n')}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
