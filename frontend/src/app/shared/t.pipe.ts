import { Pipe, PipeTransform, inject } from '@angular/core';
import { I18nService } from '../core/i18n.service';

/** {{ 'nav.catalog' | t }} — impure so it re-renders when the language signal changes. */
@Pipe({ name: 't', pure: false })
export class TPipe implements PipeTransform {
  private i18n = inject(I18nService);
  transform(key: string): string {
    return this.i18n.t(key);
  }
}

/** {{ product | loc:'name' }} → product.name_en or product.name_ru */
@Pipe({ name: 'loc', pure: false })
export class LocPipe implements PipeTransform {
  private i18n = inject(I18nService);
  transform(obj: any, base: string): string {
    return this.i18n.field(obj, base);
  }
}

/** 24900 → "24 900 ₸" */
@Pipe({ name: 'kzt' })
export class KztPipe implements PipeTransform {
  transform(value: string | number): string {
    return Math.round(Number(value)).toLocaleString('ru-RU').replace(/,/g, ' ') + ' ₸';
  }
}
