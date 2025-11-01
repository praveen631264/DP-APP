import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { Subscription } from 'rxjs';

import { DashboardService, DashboardStats } from '../services/dashboard.service';
import { DocumentService, PaginatedDocumentsResponse } from '../services/document.service';
import { Document } from '../models/document.model';
import { NgxChartsModule } from '@swimlane/ngx-charts';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [CommonModule, NgxChartsModule, MatCardModule, MatListModule, MatIconModule],
})
export class DashboardComponent implements OnInit, OnDestroy {

  public stats!: DashboardStats;
  public documents: Document[] = [];
  private refreshSubscription!: Subscription;

  constructor(
    private dashboardService: DashboardService,
    private documentService: DocumentService
  ) { }

  ngOnInit(): void {
    this.loadData();
    this.refreshSubscription = this.dashboardService.onRefreshNeeded().subscribe(() => {
      this.loadData();
    });
  }

  ngOnDestroy(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  loadData(): void {
    this.dashboardService.getStats().subscribe(stats => {
      this.stats = stats;
    });

    this.documentService.getDocuments({ page: 1, limit: 5, sort_by: 'created_at', sort_order: 'desc' }).subscribe((data: PaginatedDocumentsResponse) => {
      this.documents = data.items;
    });
  }

  objectToChartData(data: { [key: string]: number }): { name: string; value: number }[] {
    if (!data) {
      return [];
    }
    return Object.keys(data).map(key => ({ name: key, value: data[key] }));
  }
}
