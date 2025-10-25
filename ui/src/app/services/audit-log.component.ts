import { Component, OnInit, ViewChild } from '@angular/core';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatTableDataSource } from '@angular/material/table';
import { AdminService, AuditLog } from '../services/admin.service';
import { tap, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { FormBuilder, FormGroup } from '@angular/forms';

@Component({
  selector: 'app-audit-log',
  templateUrl: './audit-log.component.html',
  styleUrls: ['./audit-log.component.scss']
})
export class AuditLogComponent implements OnInit {

  dataSource = new MatTableDataSource<any>();
  displayedColumns: string[] = ['timestamp', 'user_email', 'action', 'ip_address', 'details'];
  totalLogs = 0;
  pageSize = 50;
  filterForm: FormGroup;

  @ViewChild(MatPaginator) paginator!: MatPaginator;

  constructor(private adminService: AdminService, private fb: FormBuilder) {
    this.filterForm = this.fb.group({
      action: [''],
      user_email: ['']
    });
  }

  ngOnInit(): void {
    this.loadLogs(0);

    this.filterForm.valueChanges.pipe(
      debounceTime(500),
      distinctUntilChanged()
    ).subscribe(() => {
      this.paginator.firstPage();
      this.loadLogs(0);
    });
  }

  loadLogs(pageIndex: number): void {
    this.adminService.getAuditLog(pageIndex + 1, this.pageSize, this.filterForm.value).pipe(
      tap((response: AuditLog) => {
        this.totalLogs = response.total;
        this.dataSource.data = response.items;
      })
    ).subscribe();
  }

  onPageChange(event: PageEvent): void {
    this.loadLogs(event.pageIndex);
  }
}