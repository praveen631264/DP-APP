import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Theme {
  name: string;
  displayName: string;
}

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private renderer: Renderer2;
  private _activeTheme$ = new BehaviorSubject<string>('default-light');
  activeTheme$ = this._activeTheme$.asObservable();

  availableThemes: Theme[] = [
    { name: 'default-light', displayName: 'Default Light' },
    { name: 'default-dark', displayName: 'Default Dark' },
    { name: 'deep-purple-amber', displayName: 'Deep Purple & Amber' }
  ];

  constructor(rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
    // Theme is now set by AuthService upon login
  }

  setTheme(themeName: string): void {
    const oldThemeName = this._activeTheme$.value;
    this.renderer.removeClass(document.body, `theme-${oldThemeName}`);
    
    this.renderer.addClass(document.body, `theme-${themeName}`);
    localStorage.setItem('theme', themeName);
    this._activeTheme$.next(themeName);
  }

  getActiveTheme(): Observable<string> {
    return this.activeTheme$;
  }
}