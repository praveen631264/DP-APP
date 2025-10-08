import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Category {
  id: string;
  name: string;
  description: string;
  docCount?: number;
}

@Injectable({
  providedIn: 'root'
})
export class CategoryService {

  private apiUrl = 'http://localhost:8080/api/categories';

  constructor(private http: HttpClient) { }

  getCategories(): Observable<{ categories: Category[] }> {
    return this.http.get<{ categories: Category[] }>(this.apiUrl);
  }

  addCategory(name: string, description: string): Observable<Category> {
    return this.http.post<Category>(this.apiUrl, { name, description });
  }

  deleteCategory(name: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${name}`);
  }
}
