import { useEffect } from 'react'
import { X } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import type { components } from '@/api/schema'
import { dateTime, money, renewal, shortDate, text } from '@/lib/format'
import FamilyChip from './FamilyChip'
import { ErrorBlock } from './StateBlocks'

type Asset = components['schemas']['AssetOut']

function Field({
  label,
  children,
  mono,
}: {
  label: string
  children: React.ReactNode
  mono?: boolean
}) {
  return (
    <div className="grid grid-cols-[9rem_1fr] gap-3 border-b border-slate-100 py-2.5 text-sm">
      <dt className="text-slate-500">{label}</dt>
      <dd className={`text-slate-900 ${mono ? 'break-all font-mono text-[13px]' : ''}`}>
        {children}
      </dd>
    </div>
  )
}

export default function AssetPanel({
  asset,
  error,
  onClose,
}: {
  asset: Asset | null
  error: string | null
  onClose: () => void
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <AnimatePresence>
      {asset && (
        <>
          <motion.div
            key="scrim"
            className="fixed inset-0 z-20 bg-slate-900/20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.aside
            key="panel"
            role="dialog"
            aria-label={`${asset.name} details`}
            className="fixed inset-y-0 right-0 z-30 flex w-full max-w-md flex-col bg-white shadow-2xl"
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 40, opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            <div className="flex items-start justify-between gap-3 border-b border-slate-200 px-5 py-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{text(asset.name)}</h2>
                <p className="text-sm text-slate-500">{text(asset.account)}</p>
              </div>
              <button
                data-walkthrough="panel-close"
                onClick={onClose}
                aria-label="Close details"
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-blue-600"
              >
                <X className="size-5" />
              </button>
            </div>
            {error && <ErrorBlock title="Couldn't load the latest details" message={error} />}
            <dl className="flex-1 overflow-y-auto px-5 py-2">
              <Field label="Asset name">{text(asset.name)}</Field>
              <Field label="Account">{text(asset.account)}</Field>
              <Field label="Product code">{text(asset.product_code)}</Field>
              <Field label="Product family">
                <FamilyChip family={asset.family} />
              </Field>
              <Field label="Lifecycle value">{money(asset.lifecycle_value)}</Field>
              <Field label="Current MRR">{money(asset.mrr)}</Field>
              <Field label="Lifecycle start">{shortDate(asset.lifecycle_start)}</Field>
              <Field label="Lifecycle end">{shortDate(asset.lifecycle_end)}</Field>
              <Field label="Renewal term">{renewal(asset.renewal_term, asset.renewal_unit)}</Field>
              <Field label="Owner">{text(asset.owner)}</Field>
              <Field label="Created">{dateTime(asset.created_date)}</Field>
              <Field label="Salesforce Id" mono>
                {asset.id}
              </Field>
            </dl>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
