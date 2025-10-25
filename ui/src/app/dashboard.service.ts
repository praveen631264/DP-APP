import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';

export interface CardStats {
  totalDocuments: number;
  processedDocuments: number;
  pendingDocuments: number;
  failedDocuments: number;
}

export interface ChartData {
  name: string;
  value: number;
}

export interface TimeSeriesData {
  name: string;
  series: ChartData[];
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private apiUrl = '/api/v1/dashboard';

  constructor(private http: HttpClient) { }

  getCardStats(): Observable<CardStats> {
    return this.http.get<CardStats>(`${this.apiUrl}/stats`);
  }

  getDocumentsByCategory(): Observable<ChartData[]> {
    return this.http.get<ChartData[]>(`${this.apiUrl}/documents_by_category`);
  }

  getDocumentsOverTime(): Observable<TimeSeriesData[]> {
    return this.http.get<TimeSeriesData[]>(`${this.apiUrl}/documents_over_time`);
  }
}