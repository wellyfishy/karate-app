from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('', Home.as_view(), name="home"),
    path('kelevent/', kelEvent.as_view(), name="kelevent"),
    path('kelevent/<slug:slug>/', keldetailEvent.as_view(), name="keldetail"),
    path('kelevent/<slug:slug>/atlet/', keldetailAtlet.as_view(), name="keldetailatlet"),
    path('kelevent/<slug:slug>/atlet/internal/', kelinternalAtlet.as_view(), name="kelinternalatlet"),
    path('kelevent/<slug:slug>/atlet/external/', kelexternalAtlet.as_view(), name="kelexternalatlet"),
    path('kelevent/<slug:slug>/atlet/import/', importAtlet.as_view(), name="atletimport"),
    path('kelevent/<slug:slug>/tatami/', keldetailTatami.as_view(), name="keldetailtatami"),
    path('kelevent/<slug:slug>/kata/', keldetailKata.as_view(), name="keldetailkata"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/', keldetailKategori.as_view(), name="keldetailkategori"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:pk>/', keldetailBagan.as_view(), name="keldetailbagan"),
    path('kelevent/<slug:event_slug>/kata/<int:tatami_pk>/jurypanel', JuryPanel1.as_view(), name="jurypanel1"),
    path('kelevent/<slug:event_slug>/kata/<int:tatami_pk>/jurypanel/send', views.jurysendscore, name="sendscore"),
    # path('kelevent/<slug:event_slug>/kata/<int:tatami_pk>/jurypanel/send_score', views.send_score_view, name="jurypanel1"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/detail', DetailBagan.as_view(), name="detailbagan"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/leave', LeaveControlPanel.as_view(), name="leavecontrolpanel"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/', controlPanel1.as_view(), name="controlpanel1"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/total', views.totalnilai, name="totalnilai1"),
    # path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/test', views.test, name="test"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/scoringboard/', scoringBoard1.as_view(), name="scoringboard1"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/start_timer/', StartTimer1.as_view(), name='starttimer1'),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/timer_status/', TimerStatus1.as_view(), name='timerstatus1'),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/<int:bagan_pk>/<int:detailbagan_pk>/<int:tatami_pk>/pause_timer/', PauseTimer1.as_view(), name='pausetimer1'),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/internal/', keldetailKategoriInternal.as_view(), name="keldetailkategoriinternal"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/external/', keldetailKategoriExternal.as_view(), name="keldetailkategoriexternal"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/tambah/', keltambahBagan.as_view(), name="keltambahbagan"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/tambah/internal/', keltambahBaganTest.as_view(), name="keltambahbaganinternal"),
    path('kelevent/<slug:event_slug>/kata/<slug:kategori_slug>/<str:jenis_kelamin>/tambah/external/', keltambahBaganTest.as_view(), name="keltambahbaganexternal"),
    path('event/', listEvent.as_view(), name="listevent"),
    path('event/<slug:slug>', detailEvent.as_view(), name="detailevent"),
    path('login/', Login.as_view(), name="login"),
    path('logout/', Logout.as_view(), name='logout'),
    path('dummy/', dummy.as_view(), name='dummy'),
    path('main', Main.as_view(), name='main'),
    path('<slug>', Dashboard.as_view(), name='dashboard'),
    path('<slug>/chart', ChartData.as_view(), name='chart'),

]
