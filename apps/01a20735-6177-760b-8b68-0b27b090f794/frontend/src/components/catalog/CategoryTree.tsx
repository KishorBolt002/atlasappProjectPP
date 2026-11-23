import { useState } from 'react'
import { ChevronRight, FolderTree } from 'lucide-react'
import type { CatalogSummary, CategoryNode } from '@/lib/catalog'

type Selection = { catalogId: string | null; categoryId: string | null }

type Props = {
  catalogs: CatalogSummary[]
  selection: Selection
  onSelect: (s: Selection) => void
}

function rowCls(active: boolean) {
  return `flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors focus-visible:outline-2 focus-visible:outline-cobalt ${
    active ? 'bg-cobalt text-white' : 'text-ink hover:bg-cobalt-wash'
  }`
}

function Count({ n, active }: { n: number; active: boolean }) {
  return (
    <span className={`ml-auto text-xs tabular-nums ${active ? 'text-white/85' : 'text-ink-soft'}`}>
      {n}
    </span>
  )
}

function CategoryBranch({
  node,
  catalogId,
  selection,
  onSelect,
  depth,
}: {
  node: CategoryNode
  catalogId: string
  selection: Selection
  onSelect: Props['onSelect']
  depth: number
}) {
  const [open, setOpen] = useState(true)
  const active = selection.categoryId === node.sf_id
  return (
    <li>
      <div className="flex items-center" style={{ paddingLeft: depth * 14 }}>
        {node.children.length > 0 ? (
          <button
            type="button"
            aria-label={open ? `Collapse ${node.name}` : `Expand ${node.name}`}
            onClick={() => setOpen(!open)}
            className="grid size-6 shrink-0 place-items-center rounded text-ink-soft hover:bg-paper"
          >
            <ChevronRight className={`size-3.5 transition-transform ${open ? 'rotate-90' : ''}`} />
          </button>
        ) : (
          <span className="size-6 shrink-0" />
        )}
        <button
          type="button"
          aria-current={active ? 'true' : undefined}
          onClick={() => onSelect({ catalogId, categoryId: node.sf_id })}
          className={rowCls(active)}
        >
          <span className="truncate">{node.name ?? node.sf_id}</span>
          {node.is_navigational === false && (
            <span className={`text-xs ${active ? 'text-white/80' : 'text-ink-soft'}`}>hidden</span>
          )}
          <Count n={node.total_product_count} active={active} />
        </button>
      </div>
      {open && node.children.length > 0 && (
        <ul>
          {node.children.map((c) => (
            <CategoryBranch
              key={c.sf_id}
              node={c}
              catalogId={catalogId}
              selection={selection}
              onSelect={onSelect}
              depth={depth + 1}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

export function CategoryTree({ catalogs, selection, onSelect }: Props) {
  const allActive = !selection.catalogId && !selection.categoryId
  return (
    <nav aria-label="Catalogs and categories" className="space-y-4">
      <button
        type="button"
        onClick={() => onSelect({ catalogId: null, categoryId: null })}
        className={rowCls(allActive)}
      >
        <FolderTree className="size-4" /> All products
      </button>
      {catalogs.map((cat) => {
        const active = selection.catalogId === cat.sf_id && !selection.categoryId
        return (
          <div key={cat.sf_id}>
            <button
              type="button"
              aria-current={active ? 'true' : undefined}
              onClick={() => onSelect({ catalogId: cat.sf_id, categoryId: null })}
              className={`${rowCls(active)} font-bold`}
            >
              <span className="truncate">{cat.name ?? cat.sf_id}</span>
              <Count n={cat.product_count} active={active} />
            </button>
            {cat.categories.length > 0 ? (
              <ul className="mt-0.5">
                {cat.categories.map((n) => (
                  <CategoryBranch
                    key={n.sf_id}
                    node={n}
                    catalogId={cat.sf_id}
                    selection={selection}
                    onSelect={onSelect}
                    depth={0}
                  />
                ))}
              </ul>
            ) : (
              <p className="px-2 py-1 text-xs text-ink-soft">No categories in this catalog</p>
            )}
          </div>
        )
      })}
    </nav>
  )
}
