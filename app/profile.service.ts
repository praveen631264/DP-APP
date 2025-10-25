import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserProfile {
  email: string;
  roles: string[];
  mfa_enabled: boolean;
  preferences: { [key: string]: any };
}

@Injectable({
  providedIn: 'root'
})
export class ProfileService {
  private apiUrl = '/api/v1/profile';

  constructor(private http: HttpClient) { }

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(this.apiUrl);
  }

  updatePreferences(preferences: { [key: string]: any }): Observable<any> {
    return this.http.put(`${this.apiUrl}/preferences`, preferences);
  }

  changePassword(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/change-password`, payload);
  }

  setupMfa(): Observable<{ provisioning_uri: string }> {
    return this.http.post<{ provisioning_uri: string }>(`${this.apiUrl}/mfa/setup`, {});
  }

  verifyMfa(totp_code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/mfa/verify`, { totp_code });
  }

  disableMfa(totp_code: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/mfa/disable`, { totp_code });
  }
}