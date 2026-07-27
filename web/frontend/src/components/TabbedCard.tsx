import * as React from 'react'
import { cn } from '@/lib/utils'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export interface PanelTab {
  id: string
  label: string
  content: React.ReactNode
}

/**
 * A card whose header carries a compact tab strip.
 *
 * Panels below the chart get a fixed height so they never steal room from it,
 * which means only one view fits at a time. The first tab is the live graphic --
 * the thing worth watching during playback -- and the reference figures sit one
 * click away rather than pushing the chart off the screen.
 */
export function TabbedCard({
  title,
  tabs,
  className,
}: {
  title: string
  tabs: PanelTab[]
  className?: string
}) {
  const [selected, setSelected] = React.useState(tabs[0]?.id ?? '')

  // Tabs come and go with the data (a frame with no regime shifts drops that
  // tab), so resolve rather than store -- a stale id would render nothing.
  const value = tabs.some((tab) => tab.id === selected) ? selected : (tabs[0]?.id ?? '')

  return (
    <Card className={cn('min-h-0 overflow-hidden', className)}>
      <Tabs
        value={value}
        onValueChange={setSelected}
        className="flex min-h-0 flex-1 flex-col"
      >
        <CardHeader className="shrink-0 px-3 pt-2 pb-1.5">
          <CardTitle className="truncate">{title}</CardTitle>
          {tabs.length > 1 ? (
            <TabsList className="shrink-0 gap-0 p-px">
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className="px-1.5 py-0.5 text-[10px] font-medium"
                >
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
          ) : null}
        </CardHeader>

        <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-2.5">
          {tabs.map((tab) => (
            <TabsContent key={tab.id} value={tab.id}>
              {tab.content}
            </TabsContent>
          ))}
        </div>
      </Tabs>
    </Card>
  )
}
