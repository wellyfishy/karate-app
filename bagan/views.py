from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse
from django.http import JsonResponse
from django.views.generic import View
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import *
from tablib import Dataset
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max, Sum
from faker import Faker
from django.core.exceptions import ObjectDoesNotExist
from channels.layers import get_channel_layer
from .consumers import ControlPanelConsumer
import json

fake = Faker()

class Main(View):
    def get(self, request):
        qs = Statistic.objects.all()
        return render(request, 'event/main.html', {'qs': qs,})
    
    def post(self, request):
        new_stat = request.POST.get('new-statistic')
        obj, _ = Statistic.objects.get_or_create(name=new_stat)
        return redirect('dashboard', obj.slug)
    
class Dashboard(View):
    def get(self, request, slug):
        obj = get_object_or_404(Statistic, slug=slug)
        context = {
            'name': obj.name,
            'slug': obj.slug,
            'data': obj.data,
            'user': request.user.username if request.user.username else fake.name()
        }
        return render(request, 'event/dashboard.html', context)
    
class ChartData(View):
    def get(self, request, slug):
        obj = get_object_or_404(Statistic, slug=slug)
        qs = obj.data.values('owner').annotate(Sum('value'))
        chart_data = [x["value__sum"] for x in qs]
        chart_labels = [x["owner"] for x in qs]
        return JsonResponse({
            "chartData": chart_data,
            "chartLabels": chart_labels,
        })
        
class Home(View):
    def get(self, request):
        return render(request, 'home.html')

class Login(View):
    def get(self, request):
        return render(request, 'login.html')
    
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if hasattr(user, 'jury'):
                tatami = Tatami.objects.filter(id_jury=user.jury).first()
                print(tatami)
                if tatami:
                    event = Event.objects.filter(id_tatami=tatami).first()
                    event_slug = event.slug
                    tatami_pk = tatami.pk
                    return redirect('jurypanel1', event_slug=event_slug, tatami_pk=tatami_pk)
            return redirect('home')
        else:
            return render(request, 'login.html')

class Logout(View):
    def get(self, request):
        logout(request)
        return render(request, 'home.html')

class listEvent(View):
    def get(self, request):
        event = Event.objects.all()
        context = {
            'event': event,
        }
        return render(request, 'event.html', context)

class detailEvent(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        kata = event.id_bagan.filter(kategori='Kata')
        kumite = event.id_bagan.filter(kategori='Kumite')
        context =  {
            'event': event,
            'kata': kata,
            'kumite': kumite,
        }
        print('hello')
        return render(request, 'detailevent.html', context)
    
class kelEvent(View):
    def get(self, request):
        event = Event.objects.all()
        context = {
            'event': event,
        }
        return render(request, 'kelevent.html', context)

class keldetailEvent(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan_kategori = event.bagan_kategori.all()
        kata = event.id_bagan.filter(kategori='kata')
        kumite = event.id_bagan.filter(kategori='kumite')
        context =  {
            'event': event,
            'kata': kata,
            'kumite': kumite,
            'bagan_kategori': bagan_kategori,
        }
        return render(request, 'event/index.html', context)
    
class keldetailKata(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        kata = event.id_bagan.filter(kategori='kata')
        bagan_kategori = event.bagan_kategori.all()
        context = {
            'event': event,
            'kata': kata,
            'bagan_kategori': bagan_kategori,
        }
        return render(request, 'event/kelkata.html', context)
    
class keldetailAtlet(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan = event.id_bagan.all()
        bagan_kategori = event.bagan_kategori.all()
        atlet_putra = event.id_atlet.filter(jenis_kelamin='putra')
        atlet_putri = event.id_atlet.filter(jenis_kelamin='putri')
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
        }
        return render(request, 'event/atlet.html', context)
    
class keldetailTatami(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan = event.id_bagan.all()
        bagan_kategori = event.bagan_kategori.all()
        tatami = event.id_tatami.all()
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'tatami': tatami,
        }
        return render(request, 'event/tatami.html', context)
    
    def post(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
    
        # Check if any Tatami objects exist for the current event
        if event.id_tatami.exists():
            # Get the maximum Tatami number for the current event
            max_number = event.id_tatami.aggregate(Max('number'))['number__max']
            
            # If a maximum number exists, create a Tatami with the next number
            if max_number:
                tatami_number = max_number + 1
            else:
                tatami_number = 1
        else:
            tatami_number = 1
        
        # Create the Tatami object with the assigned number and link it to the event
        tatami = Tatami.objects.create(tatami=f'Tatami {tatami_number}', number=tatami_number)
        event.id_tatami.add(tatami)

        # Create 7 juries (user) each tatami and assign it to the currently created tatami
        for i in range(7):
            username = f"tatami{tatami_number}jury{i+1}"  # Generate a custom username

            # Create a user object with the same password as the username
            user = User.objects.create_user(username=username, password=username)
            
            # Create a jury object and link it to the user
            jury = Jury.objects.create(id_user=user)
            tatami.id_jury.add(jury)
            jury.number = f'{i+1}'
            jury.save()

        return redirect('keldetailtatami', slug=slug)

class kelinternalAtlet(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan_kategori = event.bagan_kategori.all()
        atlet_putra = event.id_atlet.filter(jenis_kelamin='putra', jenis_event='internal')
        atlet_putri = event.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
        }
        return render(request, 'event/atlet.html', context)
    
class kelexternalAtlet(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan_kategori = event.bagan_kategori.all()
        atlet_putra = event.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri = event.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
        }
        return render(request, 'event/atlet.html', context)

class keldetailKategori(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri')

        bagan = event.id_bagan.filter(kategori_kata=kategori, jenis_kelamin=jenis_kelamin).order_by('-tanggal_dibuat')

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan': bagan,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
        }
        return render(request, 'event/kategorikata.html', context)

class keldetailBagan(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        bagan = get_object_or_404(Bagan, id_bagan=pk)
        detail_bagan = bagan.id_detailbagan.filter(bagan=bagan)
        tatami = event.id_tatami.all()
        
        atlet_list = []
        for detail in detail_bagan:
            atlet_list.extend(detail.id_atlet.all())
        
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan': bagan,
            'detail_bagan': detail_bagan,
            'kategori': kategori,
            'atlet_list': atlet_list,
            'tatami': tatami,
        }
        return render(request, 'event/detailbagan.html', context)
    
class DetailBagan(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        bagan = get_object_or_404(Bagan, id_bagan=bagan_pk)
        detail_bagan = bagan.id_detailbagan.filter(bagan=bagan)
        tatami = event.id_tatami.all()
        
        atlet_list = []
        for detail in detail_bagan:
            atlet_list.extend(detail.id_atlet.all())
        
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan': bagan,
            'detail_bagan': detail_bagan,
            'kategori': kategori,
            'atlet_list': atlet_list,
            'tatami': tatami,
        }
        return render(request, 'event/viewdetailbagan.html', context)
    
class JuryPanel1(View):
    def get(self, request, event_slug, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        tatami = event.id_tatami.get(pk=tatami_pk)
        
        try:
            detailbagan = DetailBagann.objects.get(id_tatami=tatami)
            atlet1 = detailbagan.id_atlet.first()
            atlet2 = detailbagan.id_atlet.last()
        except ObjectDoesNotExist:
            # Perform your desired action here
            detailbagan = None
            atlet1 = None
            atlet2 = None
            
        jury = request.user.jury
        jury_number = jury.number
        
        context = {
            'event': event,
            'tatami': tatami,
            'detailbagan': detailbagan,
            'atlet1': atlet1,
            'atlet2': atlet2,
        }
        return render(request, 'event/jury.html', context)
    
from asgiref.sync import async_to_sync
def jurysendscore(request, event_slug, tatami_pk):
    channel_layer = get_channel_layer()
    event = get_object_or_404(Event, slug=event_slug)
    tatami = event.id_tatami.get(pk=tatami_pk)
        
    try:
        detailbagan = DetailBagann.objects.get(id_tatami=tatami)
        room_name = f'ring_{tatami_pk}_{detailbagan.pk}'
    except DetailBagann.DoesNotExist:
        detailbagan = None
    
    if detailbagan.id_score.exists():
        score = detailbagan.id_score.first()
    else:
        score = Score.objects.create()
        detailbagan.id_score.add(score)
    
    jury = request.user.jury
    jury_number = jury.number
    
    input1 = request.POST.get('input1')
    input2 = request.POST.get('input2')
    
    # Get the count of existing ScoreDetail objects associated with the current user's Jury
    scoredetail_count = ScoreDetail.objects.filter(id_jury__id_user=request.user, score=score).count()  
        
    if detailbagan.id_atlet.count() == 2:
        atlet1 = detailbagan.id_atlet.first()
        atlet2 = detailbagan.id_atlet.last()
        
        if scoredetail_count > 0:
        #     # Update existing ScoreDetail object
            scoredetail1 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=1)
            scoredetail1.jury_score = input1
            atlet1.id_score.add(scoredetail1)
            atlet1.save()
            scoredetail1.save()
            scoredetail2 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=2)
            scoredetail2.jury_score = input2
            atlet2.id_score.add(scoredetail2)
            atlet2.save()
            scoredetail2.save()
        
        else:
            # Create a new ScoreDetail object
            scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
            scoredetail1.id_jury.add(jury)
            scoredetail1.nama = f"Jury {jury_number}"
            scoredetail1.number = f'1'
            scoredetail1.save()
            atlet1.id_score.add(scoredetail1)
            atlet1.save()
            scoredetail2 = ScoreDetail.objects.create(jury_score=input2)
            scoredetail2.id_jury.add(jury)
            scoredetail2.nama = f"Jury {jury_number}"
            scoredetail2.number = f'2'
            scoredetail2.save()
            atlet2.id_score.add(scoredetail2)
            atlet2.save()
    
        score.juri_score.add(scoredetail1)
        score.juri_score.add(scoredetail2)
        detailbagan.id_scoredetail.add(scoredetail1)
        detailbagan.id_scoredetail.add(scoredetail2)
        
        async_to_sync(channel_layer.group_send)(
                f"{room_name}", 
                {
                    'type': 'sendscore',
                    'sender': jury_number,
                    'message1': input1,
                    'message2': input2,
                }
            )  
        
        return redirect('jurypanel1', event_slug, tatami_pk)
    else:
        atlet1 = detailbagan.id_atlet.first()
        
        if scoredetail_count > 0:
            scoredetail1 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=1)
            scoredetail1.jury_score = input1
            atlet1.id_score.add(scoredetail1)
            atlet1.save()
            scoredetail1.save()
        else:
            scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
            scoredetail1.id_jury.add(jury)
            scoredetail1.nama = f"Jury {jury_number}"
            scoredetail1.number = f'1'
            scoredetail1.save()
            atlet1.id_score.add(scoredetail1)
            atlet1.save()
        
        score.juri_score.add(scoredetail1)
        detailbagan.id_scoredetail.add(scoredetail1)

        async_to_sync(channel_layer.group_send)(
                f"{room_name}", 
                {
                    'type': 'sendscore',
                    'sender': jury_number,
                    'message1': input1,
                    'message2': input2,
                }
            )    
        return redirect('jurypanel1', event_slug, tatami_pk)

class controlPanel1(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        atlet = detailbagan.id_atlet.all()
        atlet1 = detailbagan.id_atlet.first()
        atlet2 = detailbagan.id_atlet.last()
        
        juri1 = tatami.id_jury.get(number=1)
        juri2 = tatami.id_jury.get(number=2)
        juri3 = tatami.id_jury.get(number=3)
        juri4 = tatami.id_jury.get(number=4)
        juri5 = tatami.id_jury.get(number=5)
        
        score = detailbagan.id_score.first()

        if detailbagan.id_tatami is not None:
            print('udah ada yang punya YAHAHHAHA HAYYUUUKK')
            if detailbagan.id_tatami == tatami_pk:
                print('CIIIEEEE TATAMI INI YANG PUNYA')
            else:
                print('bruh')
        
        if score is not None:
            score1 = score.juri_score.filter(number=1)
            score2 = score.juri_score.filter(number=2)
        
            score1j1 = score1.filter(number=1, id_jury=juri1).first()
            score1j2 = score1.filter(number=1, id_jury=juri2).first()
            score1j3 = score1.filter(number=1, id_jury=juri3).first()
            score1j4 = score1.filter(number=1, id_jury=juri4).first()
            score1j5 = score1.filter(number=1, id_jury=juri5).first()
            
            score2j1 = score2.filter(number=2, id_jury=juri1).first()
            score2j2 = score2.filter(number=2, id_jury=juri2).first()
            score2j3 = score2.filter(number=2, id_jury=juri3).first()
            score2j4 = score2.filter(number=2, id_jury=juri4).first()
            score2j5 = score2.filter(number=2, id_jury=juri5).first()

            totalscore = score.id_totalscore.first()
            totalscore1 = score.id_totalscore.last()

        else:
            score1j1 = 'Belum Dikirim'
            score1j2 = 'Belum Dikirim'
            score1j3 = 'Belum Dikirim'
            score1j4 = 'Belum Dikirim'
            score1j5 = 'Belum Dikirim'
            
            score2j1 = 'Belum Dikirim'
            score2j2 = 'Belum Dikirim'
            score2j3 = 'Belum Dikirim'
            score2j4 = 'Belum Dikirim'
            score2j5 = 'Belum Dikirim'

        detailbagan.penilaian = True
        detailbagan.id_tatami = tatami
        detailbagan.save()
        
        url = reverse('controlpanel1', kwargs={
            'event_slug': event.slug,
            'kategori_slug': kategori.slug,
            'jenis_kelamin': jenis_kelamin,
            'bagan_pk': bagan.pk,
            'detailbagan_pk': detailbagan.pk,
            'tatami_pk': tatami_pk,
        })
        
        url_parts = request.path.split('/')
        internal = 'internal' in url_parts
        external = 'external' in url_parts
        
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
        
        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'detailbagan': detailbagan,
            'kategori': kategori,
            'controlpanel1_url': url, 
            'internal': internal,
            'external': external,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
            'tatami': tatami,
            'atlet': atlet,
            'score1j1': score1j1,
            'score1j2': score1j2,
            'score1j3': score1j3,
            'score1j4': score1j4,
            'score1j5': score1j5,
            'score2j1': score2j1,
            'score2j2': score2j2,
            'score2j3': score2j3,
            'score2j4': score2j4,
            'score2j5': score2j5,
            'atlet1': atlet1,
            'atlet2': atlet2,
            'totalscore1': totalscore,
            'totalscore2': totalscore1,
        }
        
        return render(request, 'event/controlpanel1.html', context)

def totalnilai(request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
    event = get_object_or_404(Event, slug=event_slug)
    bagan = get_object_or_404(Bagan, pk=bagan_pk)
    bagan_kategori = event.bagan_kategori.all()
    kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
    detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
    tatami = get_object_or_404(Tatami, pk=tatami_pk)
    atlet = detailbagan.id_atlet.all()
    atlet1 = detailbagan.id_atlet.first()
    atlet2 = detailbagan.id_atlet.last()
    
    juri1 = tatami.id_jury.get(number=1)
    juri2 = tatami.id_jury.get(number=2)
    juri3 = tatami.id_jury.get(number=3)
    juri4 = tatami.id_jury.get(number=4)
    juri5 = tatami.id_jury.get(number=5)
    
    score = detailbagan.id_score.first()
    
    if score is not None:
        score1 = score.juri_score.filter(number=1)
        score2 = score.juri_score.filter(number=2)

        pk_string = "".join(str(obj.pk) for obj in score1)

        score1 = [float(obj.jury_score) for obj in score.juri_score.filter(number=1)]
        largest_score = max(score1)
        smallest_score = min(score1)

        # Exclude the first occurrence of the smallest and largest scores
        additional_number = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=1) if float(obj.jury_score) != largest_score and float(obj.jury_score) != smallest_score])
        additional_number += (score1.count(smallest_score) - 1) * smallest_score
        additional_number += (score1.count(largest_score) - 1) * largest_score

        slug_val = f'{score.pk}-{pk_string}'

        total_score, created = TotalScore.objects.get_or_create(number=1, defaults={'total': additional_number}, slug=slug_val)
        if not created:
            total_score.total = additional_number
            total_score.save()

        score.id_totalscore.add(total_score)

        if detailbagan.id_atlet.count() == 2:
            pk_string1 = "".join(str(obj.pk) for obj in score2)

            score2 = [float(obj.jury_score) for obj in score.juri_score.filter(number=2)]
            largest_score1 = max(score2)
            smallest_score1 = min(score2)

            # Exclude the first occurrence of the smallest and largest scores
            additional_number1 = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=2) if float(obj.jury_score) != largest_score1 and float(obj.jury_score) != smallest_score1])
            additional_number1 += (score2.count(smallest_score1) - 1) * smallest_score1
            additional_number1 += (score2.count(largest_score1) - 1) * largest_score1

            slug_val1 = f'{score.pk}-{pk_string1}'

            total_score1, created = TotalScore.objects.get_or_create(number=2, defaults={'total': additional_number}, slug=slug_val1)
            if not created:
                total_score1.total = additional_number
                total_score1.save()

            print(score2)
            print("Largest Score 2:", largest_score1)
            print("Smallest Score 2:", smallest_score1)
            print("Additional Number 2:", additional_number1)

            score.id_totalscore.add(total_score1)

        print(score1)
        print("Largest Score 1:", largest_score)
        print("Smallest Score 1:", smallest_score)
        print("Additional Number 1:", additional_number)

    return redirect('controlpanel1', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, bagan_pk=bagan_pk, detailbagan_pk=detailbagan_pk, tatami_pk=tatami_pk)
    
class LeaveControlPanel(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        
        detailbagan.penilaian = False
        detailbagan.id_tatami = None
        detailbagan.dinilai = True
        detailbagan.save()
        
        return redirect('keldetailbagan', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, pk=bagan_pk)

class StartTimer1(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if not detailbagan.timer_status:
            detailbagan.timer_status = True
            detailbagan.save()

        return JsonResponse({'success': True})

class TimerStatus1(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        timer_status = "Running" if detailbagan.timer_status else "Paused"
        data = {
            'timer_status': timer_status,
        }
        return JsonResponse(data)
    
class PauseTimer1(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if detailbagan.timer_status:
            detailbagan.timer_status = False
            detailbagan.save()
        return JsonResponse({'success': True})

class scoringBoard1(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        atlet1 = detailbagan.id_atlet.first()
        atlet2 = detailbagan.id_atlet.last()

        url = reverse('scoringboard1', kwargs={
            'event_slug': event.slug,
            'kategori_slug': kategori.slug,
            'jenis_kelamin': jenis_kelamin,
            'bagan_pk': bagan.pk,
            'detailbagan_pk': detailbagan.pk,
            'tatami_pk': tatami_pk,
        })

        url_parts = request.path.split('/')
        internal = 'internal' in url_parts
        external = 'external' in url_parts
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
        
        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'detailbagan': detailbagan,
            'kategori': kategori,
            'scoringboard1_url': url, 
            'internal': internal,
            'external': external,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
            'tatami': tatami,
            'atlet1': atlet1,
            'atlet2': atlet2,
        }
        
        return render(request, 'event/sbkata1.html', context)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        return redirect('scoringboard1', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, bagan_pk=bagan_pk, detailbagan_pk=detailbagan_pk, tatami_pk=tatami_pk)

class keldetailKategoriInternal(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        bagan = event.id_bagan.filter(kategori_kata=kategori, jenis_kelamin=jenis_kelamin, jenis_event='internal')
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='internal')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
        }
        return render(request, 'event/kategorikata.html', context)

class keldetailKategoriExternal(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        bagan = event.id_bagan.filter(kategori_kata=kategori, jenis_kelamin=jenis_kelamin, jenis_event='external')
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')
        putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'putraexternal_url': putraexternal_url,
            'putriexternal_url': putriexternal_url,
        }
        return render(request, 'event/kategorikata.html', context)

class keltambahBagan(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

        # Get the URL for putra external
        putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'putraexternal_url': putraexternal_url,
            'putriexternal_url': putriexternal_url,
        }
        return render(request, 'event/tambahbagan.html', context)

class keltambahBaganTest(View):
    def post(self, request, event_slug, kategori_slug, jenis_kelamin):
        team1_value = request.POST.getlist('team1')
        team2_value = request.POST.getlist('team2')
        team3_value = request.POST.getlist('team3')
        team4_value = request.POST.getlist('team4')
        team5_value = request.POST.getlist('team5')
        team6_value = request.POST.getlist('team6')
        team7_value = request.POST.getlist('team7')
        team8_value = request.POST.getlist('team8')
        
        event = get_object_or_404(Event, slug=event_slug)
        bgn_kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        jenis_kelamin_display = dict(Atlet.JENIS_KELAMIN).get(jenis_kelamin)
        
        is_external = 'external' in request.path  
          
        counter = 0
        group = chr(ord('A') + counter)

        url_condition = 'External' if is_external else 'Internal'
        
        while Bagan.objects.filter(judul_bagan__icontains=f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group {group} - {url_condition}').exists():
            counter += 1
            group = chr(ord('A') + counter)

        judul_bagan = f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group {group} - {url_condition}'
        if url_condition == 'External':
            bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='external')
        else:
            bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='internal')
            
        event.id_bagan.add(bagan)
        bagan.kategori_kata.set([bgn_kategori])
        
        # Round 1
        for i in range(len(team1_value)):
            if team1_value[i] or team2_value[i]:
                detail_bagan = DetailBagann.objects.create(round=1)
                bagan.id_detailbagan.add(detail_bagan)
                
                for atlet_nama in [team1_value[i], team2_value[i]]:
                    if atlet_nama:
                        try:
                            atlet = Atlet.objects.get(id_atlet=atlet_nama)
                            detail_bagan.id_atlet.add(atlet)
                        except Atlet.DoesNotExist:
                            print(f"Atlet with nama_atlet='{atlet_nama}' does not exist.")
                    else:
                        print("Empty atlet_nama encountered. Skipping...")

        # Round 2
        for i in range(len(team3_value)):
            if team3_value[i] or team4_value[i]:
                detail_bagan = DetailBagann.objects.create(round=2)
                bagan.id_detailbagan.add(detail_bagan)

                for atlet_nama in [team3_value[i], team4_value[i]]:
                    if atlet_nama:
                        try:
                            atlet = Atlet.objects.get(id_atlet=atlet_nama)
                            detail_bagan.id_atlet.add(atlet)
                        except Atlet.DoesNotExist:
                            print(f"Atlet with nama_atlet='{atlet_nama}' does not exist.")
                    else:
                        print("Empty atlet_nama encountered. Skipping...")

        # Round 3
        for i in range(len(team5_value)):
            if team5_value[i] or team6_value[i]:
                detail_bagan = DetailBagann.objects.create(round=3)
                bagan.id_detailbagan.add(detail_bagan)

                for atlet_nama in [team5_value[i], team6_value[i]]:
                    if atlet_nama:
                        try:
                            atlet = Atlet.objects.get(id_atlet=atlet_nama)
                            detail_bagan.id_atlet.add(atlet)
                        except Atlet.DoesNotExist:
                            print(f"Atlet with nama_atlet='{atlet_nama}' does not exist.")
                    else:
                        print("Empty atlet_nama encountered. Skipping...")

        # Round 4
        for i in range(len(team7_value)):
            if i < len(team7_value) and i < len(team8_value):
                if team7_value[i] or team8_value[i]:
                    detail_bagan = DetailBagann.objects.create(round=4)
                    bagan.id_detailbagan.add(detail_bagan)

                    for atlet_nama in [team7_value[i], team8_value[i]]:
                        if atlet_nama:
                            try:
                                atlet = Atlet.objects.get(id_atlet=atlet_nama)
                                detail_bagan.id_atlet.add(atlet)
                            except Atlet.DoesNotExist:
                                print(f"Atlet with nama_atlet='{atlet_nama}' does not exist.")
                        else:
                            # Handle the case where atlet_nama is empty or null
                            # You can choose to skip it, display an error, or handle it as per your requirements
                            print("Empty atlet_nama encountered. Skipping...")
        
        return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)
    
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        num_loops1 = [1, 2, 3, 4, 5, 6]
        num_loops2 = [1, 2, 3]
        num_loops3 = [1, 2]
        event = get_object_or_404(Event, slug=event_slug)
        bagan = event.id_bagan.all()
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        atlet_putra_internal = kategori.id_atlet.filter(event=event, jenis_kelamin='putra', jenis_event='internal')
        atlet_putri_internal = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
        atlet_putra_external = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri_external = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

        # Get the URL for putra internal
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
        putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
        url_parts = request.path.split('/')
        internal = 'internal' in url_parts
        external = 'external' in url_parts

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori, 
            'atlet_putra_internal': atlet_putra_internal,
            'atlet_putri_internal': atlet_putri_internal,
            'atlet_putra_external': atlet_putra_external,
            'atlet_putri_external': atlet_putri_external,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
            'putraexternal_url': putraexternal_url,
            'putriexternal_url': putriexternal_url,
            'internal': internal,
            'external': external,
            'num_loops1': num_loops1,
            'num_loops2': num_loops2,
            'num_loops3': num_loops3,
        }
        return render(request, 'event/tambahbagan.html', context)

# Import athletes class
class importAtlet(View):
    def post(self, request, slug):
        dataset = Dataset()
        new_data = request.FILES['file']  # Assuming the file input name is 'file'
        if not new_data.name.endswith('.xlsx'):
            messages.error(request, 'Invalid file format. Please upload an Excel file.')
            return redirect('keldetailatlet', slug=slug)

        imported_data = dataset.load(new_data.read(), format='xlsx')
        
        event = Event.objects.get(slug=slug)
        bagan = Bagan.objects.filter(event=event)
        
        print(imported_data)
        
        for data in imported_data:
            if len(data) >= 1:  # Check if nama_atlet value exists in data
                nama_atlet = data[0]
                jenis_event = data[1]
                jenis_kelamin = data[2]
                perguruan = data[3]
                perwakilan = data[4]
                tempat_lahir = data[5]
                tanggal_lahir = data[6]
                usia_atlet = data[7]
                berat_badan = data[8]
                atlet = Atlet(
                    nama_atlet=nama_atlet,
                    jenis_event=jenis_event,
                    jenis_kelamin=jenis_kelamin,
                    perguruan=perguruan,
                    perwakilan=perwakilan,
                    tempat_lahir=tempat_lahir,
                    tanggal_lahir=tanggal_lahir,
                    usia_atlet=usia_atlet,
                    berat_badan=berat_badan,
                )
                atlet.save()
                event.id_atlet.add(atlet)
                event.save()
            
            # Validasi Usia
            if usia_atlet is not None:
                if atlet.usia_atlet <= 7.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Pra Usia Dini')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 8 and atlet.usia_atlet <= 9.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Usia Dini')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 10 and atlet.usia_atlet <= 11.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Pra Pemula')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 12 and atlet.usia_atlet <= 13.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Pemula')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 14:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Kadet')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                
        messages.success(request, 'Data imported successfully.')
        return redirect('keldetailatlet', slug=slug)
    
# Dummy
class dummy(View):
    def get(self, request):
        return render(request, 'staticbase.html')
