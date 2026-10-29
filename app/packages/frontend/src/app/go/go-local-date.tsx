"use client";

import { useId } from "react";
import { InlineScript } from "@/components/commons/InlineScript";

function scriptString(value: string): string {
  return JSON.stringify(value).replaceAll("<", "\\u003c");
}

/** Preserve browser-local dates across UTC SSR, following the installed Next guide. */
export function GoLocalDate({ date }: { date: string }) {
  const id = useId();
  return (
    <>
      <time id={id} dateTime={date} suppressHydrationWarning>
        {new Date(date).toLocaleDateString("en-US")}
      </time>
      <InlineScript
        html={`{var n=document.getElementById(${scriptString(id)});if(n)n.textContent=new Date(${scriptString(date)}).toLocaleDateString("en-US")}`}
      />
    </>
  );
}
