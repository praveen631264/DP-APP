import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AgGridModule } from 'ag-grid-angular';
import { ColDef } from 'ag-grid-community';
import { DashboardService, DashboardStats } from './dashboard.service';
import { DocumentService, PaginatedDocumentsResponse } from '../services/document.service';
import { Document } from '../models/document.model';
import { ActionsCellRendererComponent } from './actions-cell-renderer.component';
import { NgxChartsModule } from '@swimlane/ngx-charts';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [CommonModule, AgGridModule, NgxChartsModule],
})
export class DashboardComponent implements OnInit {

  public stats!: DashboardStats;
  public documents: Document[] = [];

  public columnDefs: ColDef[] = [
    { headerName: 'Filename', field: 'filename', sortable: true, filter: true },
    { headerName: 'Status', field: 'status', sortable: true, filter: true },
    { headerName: 'Created At', field: 'created_at', sortable: true, filter: true },
    { headerName: 'Actions', cellRenderer: ActionsCellRendererComponent },
  ];

  constructor(
    private dashboardService: DashboardService,
    private documentService: DocumentService
  ) { }

  ngOnInit(): void {
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
