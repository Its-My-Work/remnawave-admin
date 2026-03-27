import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { ShieldBan, Plus, Trash2, RefreshCw, Upload } from 'lucide-react'
import client from '../api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { useHasPermission } from '../components/PermissionGate'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

// Types
interface BlockedIP {
  id: number
  ip_cidr: string
  reason: string | null
  added_by_username: string | null
  country_code: string | null
  asn_org: string | null
  expires_at: string | null
  created_at: string | null
}

interface BlockedIPListResponse {
  items: BlockedIP[]
  total: number
}

// Duration options in hours (null = forever)
const DURATION_OPTIONS: { value: string; hours: number | null }[] = [
  { value: 'forever', hours: null },
  { value: '1h', hours: 1 },
  { value: '24h', hours: 24 },
  { value: '7d', hours: 168 },
  { value: '30d', hours: 720 },
]

// API functions
const fetchBlockedIPs = async (limit: number, offset: number): Promise<BlockedIPListResponse> => {
  const { data } = await client.get('/blocked-ips', { params: { limit, offset } })
  return data
}

const createBlockedIP = async (body: { ip_cidr: string; reason?: string; expires_in_hours?: number | null }): Promise<BlockedIP> => {
  const { data } = await client.post('/blocked-ips', body)
  return data
}

const bulkBlockIPs = async (body: { ips: string[]; reason?: string; expires_in_hours?: number | null }): Promise<void> => {
  await client.post('/blocked-ips/bulk', body)
}

const deleteBlockedIP = async (id: number): Promise<void> => {
  await client.delete(`/blocked-ips/${id}`)
}

const syncBlockedIPs = async (): Promise<void> => {
  await client.post('/blocked-ips/sync')
}

// Pagination
const PAGE_SIZE = 50

export default function BlockedIPs() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const canCreate = useHasPermission('blocked_ips', 'create')
  const canDelete = useHasPermission('blocked_ips', 'delete')

  // Pagination state
  const [offset, setOffset] = useState(0)

  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<BlockedIP | null>(null)

  // Add form state
  const [addIpCidr, setAddIpCidr] = useState('')
  const [addReason, setAddReason] = useState('')
  const [addDuration, setAddDuration] = useState('forever')

  // Bulk form state
  const [bulkIps, setBulkIps] = useState('')
  const [bulkReason, setBulkReason] = useState('')
  const [bulkDuration, setBulkDuration] = useState('forever')

  // Query
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['blocked-ips', offset],
    queryFn: () => fetchBlockedIPs(PAGE_SIZE, offset),
    placeholderData: (prev) => prev,
  })

  const items = Array.isArray(data?.items) ? data.items : []
  const total = data?.total ?? 0

  // Mutations
  const addMutation = useMutation({
    mutationFn: createBlockedIP,
    onSuccess: () => {
      toast.success(t('blockedIPs.addSuccess'))
      queryClient.invalidateQueries({ queryKey: ['blocked-ips'] })
      resetAddForm()
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || t('blockedIPs.addError'))
    },
  })

  const bulkMutation = useMutation({
    mutationFn: bulkBlockIPs,
    onSuccess: () => {
      toast.success(t('blockedIPs.bulkSuccess'))
      queryClient.invalidateQueries({ queryKey: ['blocked-ips'] })
      resetBulkForm()
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || t('blockedIPs.bulkError'))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteBlockedIP,
    onSuccess: () => {
      toast.success(t('blockedIPs.deleteSuccess'))
      queryClient.invalidateQueries({ queryKey: ['blocked-ips'] })
      setDeleteTarget(null)
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || t('blockedIPs.deleteError'))
    },
  })

  const syncMutation = useMutation({
    mutationFn: syncBlockedIPs,
    onSuccess: () => {
      toast.success(t('blockedIPs.syncSuccess'))
      queryClient.invalidateQueries({ queryKey: ['blocked-ips'] })
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || t('blockedIPs.syncError'))
    },
  })

  // Helpers
  const getDurationHours = (value: string): number | null => {
    return DURATION_OPTIONS.find((d) => d.value === value)?.hours ?? null
  }

  const resetAddForm = useCallback(() => {
    setAddDialogOpen(false)
    setAddIpCidr('')
    setAddReason('')
    setAddDuration('forever')
  }, [])

  const resetBulkForm = useCallback(() => {
    setBulkDialogOpen(false)
    setBulkIps('')
    setBulkReason('')
    setBulkDuration('forever')
  }, [])

  const handleAdd = () => {
    if (!addIpCidr.trim()) return
    const hours = getDurationHours(addDuration)
    addMutation.mutate({
      ip_cidr: addIpCidr.trim(),
      reason: addReason.trim() || undefined,
      expires_in_hours: hours,
    })
  }

  const handleBulk = () => {
    const ips = bulkIps
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
    if (ips.length === 0) return
    const hours = getDurationHours(bulkDuration)
    bulkMutation.mutate({
      ips,
      reason: bulkReason.trim() || undefined,
      expires_in_hours: hours,
    })
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return dateStr
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1

  return (
    <div className="flex flex-col gap-4 p-4 sm:p-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <ShieldBan className="h-6 w-6 text-red-500" />
          <h1 className="text-xl font-semibold sm:text-2xl">{t('blockedIPs.title')}</h1>
          {!isLoading && (
            <span className="text-sm text-muted-foreground">({total})</span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {canCreate && (
            <>
              <Button size="sm" onClick={() => setAddDialogOpen(true)}>
                <Plus className="mr-1 h-4 w-4" />
                {t('blockedIPs.addIP')}
              </Button>
              <Button size="sm" variant="outline" onClick={() => setBulkDialogOpen(true)}>
                <Upload className="mr-1 h-4 w-4" />
                {t('blockedIPs.bulkBlock')}
              </Button>
            </>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={`mr-1 h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            {t('blockedIPs.sync')}
          </Button>
        </div>
      </div>

      <Separator />

      {/* Table */}
      <div className="overflow-x-auto rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t('blockedIPs.columns.ipCidr')}</TableHead>
              <TableHead className="hidden sm:table-cell">{t('blockedIPs.columns.country')}</TableHead>
              <TableHead className="hidden md:table-cell">{t('blockedIPs.columns.asnProvider')}</TableHead>
              <TableHead>{t('blockedIPs.columns.reason')}</TableHead>
              <TableHead className="hidden lg:table-cell">{t('blockedIPs.columns.addedBy')}</TableHead>
              <TableHead className="hidden md:table-cell">{t('blockedIPs.columns.created')}</TableHead>
              <TableHead className="hidden lg:table-cell">{t('blockedIPs.columns.expires')}</TableHead>
              {canDelete && <TableHead className="w-[60px]">{t('blockedIPs.columns.actions')}</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                  <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-8" /></TableCell>
                  <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                  <TableCell className="hidden lg:table-cell"><Skeleton className="h-4 w-16" /></TableCell>
                  <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-24" /></TableCell>
                  <TableCell className="hidden lg:table-cell"><Skeleton className="h-4 w-24" /></TableCell>
                  {canDelete && <TableCell><Skeleton className="h-8 w-8" /></TableCell>}
                </TableRow>
              ))
            ) : items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={canDelete ? 8 : 7} className="py-12 text-center text-muted-foreground">
                  {t('blockedIPs.empty')}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-mono text-sm">{item.ip_cidr}</TableCell>
                  <TableCell className="hidden sm:table-cell">
                    {item.country_code ? (
                      <span title={item.country_code}>{item.country_code}</span>
                    ) : '—'}
                  </TableCell>
                  <TableCell className="hidden md:table-cell max-w-[200px] truncate">
                    {item.asn_org || '—'}
                  </TableCell>
                  <TableCell className="max-w-[150px] truncate">{item.reason || '—'}</TableCell>
                  <TableCell className="hidden lg:table-cell">{item.added_by_username || '—'}</TableCell>
                  <TableCell className="hidden md:table-cell text-xs text-muted-foreground">
                    {formatDate(item.created_at)}
                  </TableCell>
                  <TableCell className="hidden lg:table-cell text-xs text-muted-foreground">
                    {item.expires_at ? formatDate(item.expires_at) : t('blockedIPs.forever')}
                  </TableCell>
                  {canDelete && (
                    <TableCell>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-red-500 hover:text-red-600"
                        onClick={() => setDeleteTarget(item)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {t('blockedIPs.pagination', { current: currentPage, total: totalPages })}
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={offset === 0 || isFetching}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              {t('common.previous')}
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={offset + PAGE_SIZE >= total || isFetching}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              {t('common.next')}
            </Button>
          </div>
        </div>
      )}

      {/* Add IP Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={(open) => { if (!open) resetAddForm(); else setAddDialogOpen(true) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('blockedIPs.addDialog.title')}</DialogTitle>
            <DialogDescription>{t('blockedIPs.addDialog.description')}</DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="add-ip">{t('blockedIPs.addDialog.ipCidr')}</Label>
              <Input
                id="add-ip"
                placeholder="192.168.1.0/24"
                value={addIpCidr}
                onChange={(e) => setAddIpCidr(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="add-reason">{t('blockedIPs.addDialog.reason')}</Label>
              <Input
                id="add-reason"
                placeholder={t('blockedIPs.addDialog.reasonPlaceholder')}
                value={addReason}
                onChange={(e) => setAddReason(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>{t('blockedIPs.addDialog.duration')}</Label>
              <Select value={addDuration} onValueChange={setAddDuration}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DURATION_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {t(`blockedIPs.durations.${opt.value}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={resetAddForm}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleAdd} disabled={!addIpCidr.trim() || addMutation.isPending}>
              {addMutation.isPending ? t('common.loading') : t('blockedIPs.addDialog.submit')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Block Dialog */}
      <Dialog open={bulkDialogOpen} onOpenChange={(open) => { if (!open) resetBulkForm(); else setBulkDialogOpen(true) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('blockedIPs.bulkDialog.title')}</DialogTitle>
            <DialogDescription>{t('blockedIPs.bulkDialog.description')}</DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="bulk-ips">{t('blockedIPs.bulkDialog.ips')}</Label>
              <textarea
                id="bulk-ips"
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                placeholder={t('blockedIPs.bulkDialog.ipsPlaceholder')}
                value={bulkIps}
                onChange={(e) => setBulkIps(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="bulk-reason">{t('blockedIPs.bulkDialog.reason')}</Label>
              <Input
                id="bulk-reason"
                placeholder={t('blockedIPs.addDialog.reasonPlaceholder')}
                value={bulkReason}
                onChange={(e) => setBulkReason(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>{t('blockedIPs.bulkDialog.duration')}</Label>
              <Select value={bulkDuration} onValueChange={setBulkDuration}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DURATION_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {t(`blockedIPs.durations.${opt.value}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={resetBulkForm}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleBulk} disabled={!bulkIps.trim() || bulkMutation.isPending}>
              {bulkMutation.isPending ? t('common.loading') : t('blockedIPs.bulkDialog.submit')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm Dialog */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title={t('blockedIPs.deleteDialog.title')}
        description={t('blockedIPs.deleteDialog.description', { ip: deleteTarget?.ip_cidr })}
        confirmLabel={t('common.delete')}
        variant="destructive"
        onConfirm={() => {
          if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
        }}
      />
    </div>
  )
}
