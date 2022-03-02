from django.shortcuts import render
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, F
from _decimal import Decimal

from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

now = timezone.now()


def home(request):
    return render(request, 'crm/home.html',
                  {'crm': home})


@login_required
def customer_list(request):
    customer = Customer.objects.filter()
    return render(request, 'crm/customer_list.html',
                  {'customers': customer})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        # update
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.updated_date = timezone.now()
            customer.save()
            customer = Customer.objects.filter()
            return render(request, 'crm/customer_list.html',
                          {'customers': customer})
    else:
        # edit
        form = CustomerForm(instance=customer)
    return render(request, 'crm/customer_edit.html', {'form': form})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('crm:customer_list')


@login_required
def service_list(request):
    services = Service.objects.filter(created_date__lte=timezone.now())
    return render(request, 'crm/service_list.html', {'services': services})


@login_required
def service_new(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.created_date = timezone.now()
            service.save()
            services = Service.objects.filter(created_date__lte=timezone.now())
            return render(request, 'crm/service_list.html',
                          {'services': services})
    else:
        form = ServiceForm()

    return render(request, 'crm/service_new.html', {'form': form})


@login_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()
            service.updated_date = timezone.now()
            service.save()
            services = Service.objects.filter(created_date__lte=timezone.now())
            return render(request, 'crm/service_list.html', {'services': services})
    else:
        form = ServiceForm(instance=service)
    return render(request, 'crm/service_edit.html', {'form': form})


@login_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    return redirect('crm:service_list')


@login_required
def product_list(request):
    products = Product.objects.filter(created_date__lte=timezone.now())
    return render(request, 'crm/product_list.html', {'products': products})


@login_required
def product_new(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_date = timezone.now()
            product.save()
            products = Product.objects.filter(created_date__lte=timezone.now())
            return render(request, 'crm/product_list.html',
                          {'products': products})
    else:
        form = ProductForm()

    return render(request, 'crm/product_new.html', {'form': form})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            product.updated_date = timezone.now()
            product.save()
            products = Product.objects.filter(created_date__lte=timezone.now())
            return render(request, 'crm/product_list.html', {'products': products})
    else:
        form = ProductForm(instance=product)
    return render(request, 'crm/product_edit.html', {'form': form})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('crm:product_list')


@login_required
def summary(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    services = Service.objects.filter(cust_name=pk)
    products = Product.objects.filter(cust_name=pk)
    sum_service_charge = \
        Service.objects.filter(cust_name=pk).aggregate(Sum('service_charge'))
    sum_product_charge = \
        Product.objects.filter(cust_name=pk).aggregate(Sum('charge'))

    # if no product or service records exist for the customer,
    # change the ‘None’ returned by the query to 0.00
    test1 = sum_product_charge.get("charge__sum")
    if test1 is None:
        sum_product_charge = {'charge__sum': Decimal('0')}
        test1 = 0

    test2 = sum_service_charge.get("service_charge__sum")
    if test2 is None:
        sum_service_charge = {'service_charge__sum': Decimal('0')}
        test2 = 0

    sum_total_charge = round(test1 + test2, 2)
    return render(request, 'crm/summary.html', {'customer': customer,
                                                'products': products,
                                                'services': services,
                                                'sum_service_charge': sum_service_charge,
                                                'sum_product_charge': sum_product_charge,
                                                'sum_total_charge': sum_total_charge, })


@login_required
def summary_pdf(request, pk):
    # customer = Service.objects.all
    # services = Service.objects.all
    # products = Product.objects.all
    customer = get_object_or_404(Customer, pk=pk)
    services = Service.objects.filter(cust_name=pk)
    products = Product.objects.filter(cust_name=pk)

    sum_service_charge = \
        Service.objects.aggregate(Sum('service_charge'))
    sum_product_charge = \
        Product.objects.aggregate(Sum('charge'))

    # Create a bytestream buffer to receive PDF data.
    buf = io.BytesIO()
    # Create the PDF object, using the buffer as its "file."
    c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
    # Create a text object
    textob = c.beginText()
    textob.setTextOrigin(inch, 1 * inch)
    textob.setFont("Helvetica", 14)

    test1 = sum_product_charge.get("charge__sum")

    # test1 = 1
    # test2 = 2

    if test1 is None:
        sum_product_charge = {'charge__sum': Decimal('0')}
        test1 = 0

    test2 = sum_service_charge.get("service_charge__sum")
    if test2 is None:
        sum_service_charge = {'service_charge__sum': Decimal('0')}
        test2 = 0

    sum_total_charge = round(test1 + test2, 2)
    test1 = round(test1, 2)
    test2 = round(test2, 2)
    textob.textLine("Total Product Charges:  " + str(test1))
    textob.textLine("Total Service Charges:  " + str(test2))
    textob.textLine("Grand total of Service and Product Charges: " + str(sum_total_charge))

    # Finish up
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    # Return
    return FileResponse(buf, as_attachment=True, filename='ActivitySummary.pdf')