"use client";

import { useState } from "react";import { X } from "lucide-react";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { HealthBadge } from "./health-badge";
import { ProductImage } from "./product-image";
import { ProductTabs } from "./product-tabs";
import type { Product } from "./types";

type ProductDrawerProps = {
  product: Product | null;
  onClose: () => void;
};

export function ProductDrawer({ product, onClose }: ProductDrawerProps) {
  const [current, setCurrent] = useState<Product | null>(null);
  const [prevProduct, setPrevProduct] = useState<Product | null>(null);
  const [open, setOpen] = useState(false);

  if (product !== prevProduct) {
    setPrevProduct(product);
    if (product) {
      setCurrent(product);
      setOpen(true);
    }
  }

  function handleOpenChange(nextOpen: boolean) {
    setOpen(nextOpen);
    if (!nextOpen) {
      window.setTimeout(() => {
        setCurrent(null);
        onClose();
      }, 200);
    }
  }

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent
        side="right"
        showCloseButton={false}
        className="w-full! gap-0 p-0! sm:max-w-lg!"
      >
        {current && (
          <>
            <div className="relative h-40 shrink-0 overflow-hidden">
              <ProductImage
                src={current.imageUrl}
                alt={current.name}
                sizes="512px"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/25 to-transparent" />
              <SheetClose asChild>
                <Button
                  variant="outline"
                  size="icon-sm"
                  className="absolute top-3 right-3 border-border/60 bg-background/70 backdrop-blur-sm"
                >
                  <X className="size-4" />
                  <span className="sr-only">Close product details</span>
                </Button>
              </SheetClose>
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-background via-background/70 to-transparent p-5 pt-10">
                <SheetTitle className="text-lg leading-snug">
                  {current.name}
                </SheetTitle>
                <SheetDescription className="mt-0.5">
                  {current.category}
                </SheetDescription>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-5 pb-8">
              <div className="flex flex-col gap-6 pt-4">
                <div className="flex items-center justify-between gap-3">
                  <HealthBadge health={current.health} />
                  <span className="text-xs text-muted-foreground">
                    {current.source}
                  </span>
                </div>
                <ProductTabs product={current} />
              </div>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
