import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {

  constructor() { }

  setTheme(themeName: string): void {
    // In a real implementation, this would add/remove CSS classes
    // to the body element to apply the theme.
    console.log(`Theme set to: ${themeName}`);
  }
}