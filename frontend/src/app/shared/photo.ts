import { Pipe, PipeTransform } from '@angular/core';

import { environment } from '../../environments/environment';

const BACKEND = environment.apiUrl.replace(/\/api\/?$/, '');

export function photoUrl(image: string | null | undefined): string {
  if (!image) return '';
  return image.startsWith('/') ? BACKEND + image : image;
}

/** Product photo URL: the API may return "/media/products/x.jpg" — prefix the backend address. */
@Pipe({ name: 'photo' })
export class PhotoPipe implements PipeTransform {
  transform(image: string | null | undefined): string {
    if (!image) return '';
    return image.startsWith('/') ? BACKEND + image : image;
  }
}
