import { Component, input } from '@angular/core';

/** Simple line icons per category (no external images → works offline on exam day). */
@Component({
  selector: 'app-part-icon',
  template: `
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" [attr.width]="size()" [attr.height]="size()">
      @switch (name()) {
        @case ('disc') { <circle cx="24" cy="24" r="18"/><circle cx="24" cy="24" r="6"/><path d="M24 6v6M24 36v6M6 24h6M36 24h6"/> }
        @case ('droplet') { <path d="M24 6c7 9 12 15 12 22a12 12 0 0 1-24 0c0-7 5-13 12-22z"/><path d="M18 30a6 6 0 0 0 6 6"/> }
        @case ('filter') { <path d="M8 10h32l-12 14v12l-8 4V24z"/> }
        @case ('bulb') { <path d="M18 34h12M20 40h8"/><path d="M24 6a11 11 0 0 0-7 19.5c1.3 1.1 2 2.6 2 4.5h10c0-1.9.7-3.4 2-4.5A11 11 0 0 0 24 6z"/> }
        @case ('spring') { <path d="M16 6h16M16 42h16M16 10l16 4-16 4 16 4-16 4 16 4-16 4 16 4"/> }
        @case ('wheel') { <circle cx="24" cy="24" r="18"/><circle cx="24" cy="24" r="10"/><circle cx="24" cy="24" r="2"/><path d="M24 14v8M24 26v8M14 24h8M26 24h8"/> }
        @case ('spark') { <path d="M20 6h8v8h-8z"/><path d="M22 14v6h4v-6"/><path d="M18 20h12l-2 8h-8z"/><path d="M24 28v6"/><path d="M20 38l4-4 4 4"/> }
        @case ('battery') { <rect x="6" y="14" width="36" height="26" rx="3"/><path d="M13 14v-4h6v4M29 14v-4h6v4"/><path d="M13 27h6M16 24v6M29 27h6"/> }
        @case ('thermo') { <path d="M20 8a4 4 0 0 1 8 0v19a8 8 0 1 1-8 0z"/><path d="M24 20v12"/><path d="M32 12h6M32 18h6M32 24h6"/> }
        @case ('car') { <path d="M6 32h36M9 32l4-10h22l4 10"/><path d="M15 22l3-7h12l3 7"/><circle cx="14" cy="34" r="4"/><circle cx="34" cy="34" r="4"/> }
        @case ('spray') { <rect x="16" y="18" width="14" height="24" rx="2"/><path d="M19 18v-6h8v6"/><path d="M27 12h5"/><path d="M36 8l3-2M36 12h4M36 16l3 2"/> }
        @default { <path d="M24 6l5.5 11.2 12.3 1.8-8.9 8.7 2.1 12.3L24 34.2 13 40l2.1-12.3-8.9-8.7 12.3-1.8z"/> }
      }
    </svg>
  `,
  styles: `:host { display: inline-flex; }`,
})
export class PartIcon {
  name = input<string>('star');
  size = input<number>(48);
}
