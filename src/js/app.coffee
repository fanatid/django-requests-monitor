$        = require 'jquery'
strftime = require 'jquery-strftime'
cookie   = require 'jquery-cookie'
_        = require 'underscore'
Backbone = require 'backbone'
Mustache = require 'mustache'



csrfSafeMethod = (method) ->
    return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method)

sameOrigin = (url) ->
    host      = document.location.host
    protocol  = document.location.protocol
    sr_origin = '//' + host
    origin    = protocol + sr_origin
    return (url == origin or url.slice(0, origin.length + 1) == origin + '/') or
        (url == sr_origin or url.slice(0, sr_origin.length + 1) == sr_origin + '/') or
        !(/^(\/\/|http:|https:).*/.test(url))

$.ajaxSetup
    beforeSend: (xhr, settings) ->
        if not csrfSafeMethod(settings.type) and sameOrigin(settings.url)
            xhr.setRequestHeader "X-CSRFToken", $.cookie('csrftoken')


class RequestInfoView extends Backbone.View
    initialize: (options) ->
        @model.view = @
    render: ->
        status = @model.get "status"
        status = _.first _.filter [
            [100, 200, "info"],
            [200, 300, "success"],
            [300, 400, "redirection"],
            [400, 500, "cerror"],
            [500, 600, "serror"]
        ], (data) =>
            data[0] <= status < data[1]
        context = _.extend @model.toJSON(),
            "formated_date": ($.strftime "%d/%b/%Y %H:%M:%S.", @model.get "date") + @model.get("date").getMilliseconds()
            "request_class": if status? then status[2] else null
        @el = Mustache.render $("#tpl-requests-request").text(), context
        @$el = $(@el)
        @$el.on "click", =>
            window.location.hash = "#!/r/" + @model.get "key"
        @
    remove: ->
        @$el.remove()


class RequestInfoCollection extends Backbone.Collection
    comparator: (model) ->
        -model.get("date").getTime()
    sync: ->
        $.ajax
            type: "POST"
            data:
                "keys": @pluck "key"
            success: (data, status, xhr) =>
                if data.delete? and data.delete.length > 0
                    @remove _.filter @models, (model) ->
                        model.get("key") in data.delete
                if data.new?
                    for obj in data.new
                        @add new @model
                            key:    obj.key
                            date:   new Date(obj.date)
                            method: obj.method
                            status: parseInt(obj.status)
                            path:   obj.path
    start_sync: ->
        @syncID = setInterval (=> @sync()), 1000
        @sync()
    stop_sync: ->
        clearInterval @syncID


class RequestsView extends Backbone.View
    initialize: (options) ->
        @el = $("#tpl-requests").text()
        @$el = $(@el)
    render: ->
        @requests = new RequestInfoCollection
        $target = @$el.find("tbody")
        @requests.on "add", (model, collection, options) =>
            view = new RequestInfoView
                model: model
            $el = view.render().$el
            if @$el.find("tbody >").length != 0
                if @requests.last() == model
                    @$el.find("tbody > :last").after $el
                else
                    @$el.find("tbody >").eq(@requests.indexOf(model)).before $el
            else
                @$el.find("tbody").append $el
        @requests.on "remove", (model, collection, options) =>
            model.view.remove()
        @requests.start_sync()
        @gc = setInterval (=>
            keys = @requests.pluck "key"
            @$el.find("tbody tr").each ->
                if $(@).attr("id") not in keys
                    console.log $(@)
                    $(@).remove()
        ), 5000
        @
    remove: ->
        @requests.stop_sync()
        clearInterval(@gc)
        @$el.remove()


class RequestModel extends Backbone.Model
    urlRoot: "r"


class RequestView extends Backbone.View
    initialize: (options) ->
        @el = $("#tpl-request").text()
        @$el = $(@el)
        @template_title     = Mustache.compile $("#tpl-request-title").text()
        @template_content   = Mustache.compile $("#tpl-request-content").text()
        @template_panel_nav = Mustache.compile $("#tpl-request-panel-nav").text()
    render: ->
        @model = new RequestModel
            id: @options.key
        @model.fetch
            success: (data, status, xhr) =>
                for panel, index in @model.get "panels"
                    $(@template_panel_nav _.extend _.clone(panel), "hash": '#!/r/' + @model.id + '/' + index)
                        .appendTo(@$el.find(".toolbar ul"))
                        .click ->
                            window.location.hash = $(@).find("a").data("hash")
                            return false
                if @currentPanel?
                    @set_panel @currentPanel
            error: (xhr, status, error) =>
                $("<div class=\"alert alert-error\">Cann't load request data :'(</div>")
                    .after("#navbar")
                    .fadeIn('slow')
                    .delay(5000)
                    .fadeOut 'slow', ->
                        $(@).remove()
        @
    set_panel: (panel) ->
        unless panel instanceof Object
            panel = parseInt(panel)
        unless @model.has "panels"
            @currentPanel = panel
            return
        if panel instanceof Object
            callback = panel.callback
            panel    = panel.panel
        return if isNaN(panel) or @model.get("panels").length <= panel < 0
        @currentPanel = panel
        @$el.find("ul li").eq(panel).addClass "active"
        panel = @model.get("panels")[panel]
        @$el.find(".title").show().html @template_title panel
        @$el.find(".content").html @template_content panel
        # bind click event in SQL querys
        @$el.find(".query .djDebugSql").each ->
            $(@).find(".djDebugCollapsed, .djDebugUncollapsed").on "click", (event) =>
                $(event.target).hide()
                $(@).find(if "djDebugCollapsed" in $(event.target).attr("class").split(' ') then ".djDebugUncollapsed" else ".djDebugCollapsed").show()
                return false
        @$el.find(".toggle").each (index, item) =>
            $(item).find("a").on "click", (event) =>
                $el = $(event.target)
                id = $el.data "toggle-id"
                if $("#sqlDetails_"+id).is(":visible")
                    $el.html $el.data "toggle-open"
                    $("#sqlMain_"+id).find(".query .djDebugCollapsed").trigger "click"
                    $("#sqlDetails_"+id).hide()
                else
                    $el.html $el.data "toggle-close"
                    $("#sqlMain_"+id).find(".query .djDebugUncollapsed").trigger "click"
                    $("#sqlDetails_"+id).show()
        # bind toggle context in Templates
        @$el.find("dl dd").each ->
            $(@).find("a.djTemplateShowContext").on "click", =>
                $(@).find(".djTemplateHideContextDiv").toggle()
                $(@).find("span.toggleArrow").html \
                    if $(@).find(".djTemplateHideContextDiv").is(":visible") then String.fromCharCode(0x25bc) else String.fromCharCode(0x25b6)
        @$el.find(".content").show()
        callback() if callback?
    unset_panel: ->
        @currentPanel = null
        @$el.find(".title").hide().html ""
        @$el.find(".content").hide().html ""
        @$el.find("ul li.active").removeClass "active"


class SettingsView extends Backbone.View
    render: ->
        @


class AppView extends Backbone.View
    initialize: (options) ->
        @setElement $("#container")
        @nav_request = [["Requests", "#"]]
    nav_request_refresh: ->
        $ul = $("#navbar .request").html("")
        for data, i in @nav_request
            if i == @nav_request.length-1
                inner = @nav_request[@nav_request.length-1][0]
            else
                inner = '<a href="'+data[1]+'">'+data[0]+'</a><span class="divider">/</span>'
            $("<li>"+inner+"</li>").appendTo $ul
    load_requests: ->
        @currentView.remove() if @currentView
        @currentView = new RequestsView
        @$el.html @currentView.render().$el
        @nav_request = @nav_request[0..0]
        @nav_request_refresh()
    load_request: (key) ->
        @nav_request = @nav_request[0..0]
        @nav_request.push ["Request", "#!/r/" + key]
        @nav_request_refresh()
        if @currentView? and @currentView instanceof RequestView
            @currentView.unset_panel()
            return
        @currentView.remove() if @currentView
        @currentView = new RequestView
            key: key
        @$el.html @currentView.render().$el
    load_request_panel: (key, panel) ->
        @load_request(key)
        @currentView.set_panel
            panel:    panel,
            callback: =>
                @nav_request = @nav_request[0..1] 
                @nav_request.push [
                    @currentView.model.get("panels")[@currentView.currentPanel].nav_title,
                    "#!/r/"+key+"/"+@currentView.currentPanel
                ]
                @nav_request_refresh()
    load_settings: ->
        @currentView.remove() if @currentView
        @currentView = new SettingsView
        @$el.html @currentView.render().$el


class AppRouter extends Backbone.Router
    initialize: (options) ->
        @app = new AppView
    requests: ->
        @app.load_requests()
    request: (key) ->
        @app.load_request(key)
    panel: (key, panel) ->
        @app.load_request_panel(key, panel)
    settings: ->
        @app.load_settings()
    routes:
        "":                "requests",
        "!/r/:key":        "request",
        "!/r/:key/:panel": "panel",
        "!/settings":      "settings",

$ ->
    window.router = new AppRouter
    Backbone.history.start()
