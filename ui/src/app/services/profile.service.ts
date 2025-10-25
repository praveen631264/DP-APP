import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserProfile {
  id: string;
  email: string;
  roles: string[];
  preferences: {
    theme?: string;
    [key: string]: any;
  };
  // Add other profile properties as needed
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
}