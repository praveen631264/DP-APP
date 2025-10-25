import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { jwtDecode } from 'jwt-decode';
import { ProfileService, UserProfile } from './profile.service';
import { ThemeService } from './theme.service';

interface DecodedToken {
  sub: string; // Subject (user's email)
  identity: string; // The user's ID
  exp: number; // Expiration time
  roles: string[]; // User roles
  email: string;
}

export interface AuthResponse {
  message: string;
  token?: string;
  mfa_required?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = '/api/v1/auth';
  private _isLoggedIn$ = new BehaviorSubject<boolean>(false);
  private _currentUserEmail$ = new BehaviorSubject<string | null>(null);
  private _currentUserId$ = new BehaviorSubject<string | null>(null);
  private _currentUserRoles$ = new BehaviorSubject<string[]>([]);
  isLoggedIn$ = this._isLoggedIn$.asObservable();
  currentUserEmail$ = this._currentUserEmail$.asObservable();
  currentUserId$ = this._currentUserId$.asObservable();
  currentUserRoles$ = this._currentUserRoles$.asObservable();

  constructor(
    private http: HttpClient, 
    private router: Router,
    private profileService: ProfileService,
    private themeService: ThemeService
  ) {
    const token = this.getToken();
    if (token) {
      this.initializeUserSession(token);
    }
  }

  login(credentials: { email: string, password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials).pipe(
      tap(response => {
        if (response.token) {
          this.handleAuthentication(response.token);
          this.initializeUserSession(response.token);
        }
      })
    );
  }

  loginWithMfa(email: string, totp_code: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login/mfa`, { email, totp_code }).pipe(
      tap(response => {
        if (response.token) {
          this.handleAuthentication(response.token);
          this.initializeUserSession(response.token);
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem('auth_token');
    this._isLoggedIn$.next(false);
    this._currentUserEmail$.next(null);
    this._currentUserId$.next(null);
    this._currentUserRoles$.next([]);
    this.router.navigate(['/login']);
  }

  private initializeUserSession(token: string): void {
    this.handleAuthentication(token);
    // On initial load, also fetch profile to set the theme
    this.profileService.getProfile().subscribe(profile => {
      if (profile && profile.preferences) {
        this.themeService.setTheme(profile.preferences['theme'] || 'default-light');
      }
    });
  }

  private handleAuthentication(token: string): void {
    localStorage.setItem('auth_token', token);
    this._isLoggedIn$.next(true);
    try {
      const decodedToken: DecodedToken = jwtDecode(token);
      this._currentUserId$.next(decodedToken.sub);
      this._currentUserEmail$.next(decodedToken.email);
      this._currentUserRoles$.next(decodedToken.roles || []);
    } catch (error) {
      console.error("Could not decode token", error);
    }
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  hasRole(role: string): Observable<boolean> {
    return this.currentUserRoles$.pipe(map(roles => roles.includes(role)));
  }
}