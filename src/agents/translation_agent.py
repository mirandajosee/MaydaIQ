"""Deterministic translation stub for demo-safe multilingual labels."""

from __future__ import annotations

from src.schemas import ActionPlan, AgentTraceStep, MaydaIQResult


SPANISH_DISCLAIMER = (
    "MaydaIQ no es un servicio de emergencia y no contacta autoridades reales. "
    "Use servicios locales de emergencia si hay peligro inmediato."
)


SPANISH_TEXT: dict[str, str] = {
    "Flooding may hide fast water, debris, open drains, or energized wires.": "La inundacion puede ocultar corriente rapida, escombros, desagues abiertos o cables energizados.",
    "Smoke or fire near a building can change quickly and may indicate trapped occupants.": "El humo o fuego cerca de un edificio puede cambiar rapido y podria indicar personas atrapadas.",
    "A crash with possible injury and blocked traffic needs scene safety first.": "Un choque con posible lesion y transito bloqueado requiere priorizar la seguridad de la escena.",
    "A personal safety threat should prioritize distance, escape, and official help.": "Una amenaza a la seguridad personal requiere priorizar distancia, escape y ayuda oficial.",
    "Possible active personal safety threat. Prioritize distance and escape to a safe, public, well-lit place; do not confront or pursue anyone; contact emergency services or law enforcement when safe.": "Posible amenaza activa a la seguridad personal. Priorice distancia y escape hacia un lugar seguro, publico y bien iluminado; no confronte ni persiga a nadie; contacte emergencias o autoridad policial cuando sea seguro.",
    "Electrical hazards can energize water, fences, vehicles, or nearby ground.": "Un riesgo electrico puede energizar agua, rejas, vehiculos o el suelo cercano.",
    "Water observations can screen for possible pollution, but they are not a definitive diagnosis.": "Las observaciones del agua pueden indicar posible contaminacion, pero no son un diagnostico definitivo.",
    "Lichen observations can support air-quality screening, but they cannot prove exact pollutant levels.": "Las observaciones de liquenes pueden apoyar un tamizaje de calidad del aire, pero no prueban niveles exactos de contaminantes.",
    "The report needs more detail before MaydaIQ can classify the incident confidently.": "El reporte necesita mas detalle antes de que MaydaIQ pueda clasificar el incidente con confianza.",
    "Move people to higher ground away from floodwater.": "Mueva a las personas a terreno mas alto, lejos del agua de inundacion.",
    "Keep back from wires, poles, and submerged outlets.": "Mantengase lejos de cables, postes y conexiones sumergidas.",
    "Do not walk or drive through floodwater or touch anything electrical.": "No camine ni conduzca por agua de inundacion ni toque elementos electricos.",
    "Evacuate away from smoke and heat.": "Evacue alejandose del humo y del calor.",
    "Warn nearby people only if you can do it while leaving.": "Avise a personas cercanas solo si puede hacerlo mientras se retira.",
    "Do not re-enter, open hot doors, or move toward smoke.": "No vuelva a entrar, no abra puertas calientes ni avance hacia el humo.",
    "Move to a safe area away from traffic if possible.": "Si es posible, muevase a una zona segura lejos del transito.",
    "Keep the injured person still unless there is immediate danger.": "Mantenga quieta a la persona herida salvo que haya peligro inmediato.",
    "Do not stand in traffic lanes or provide invasive medical care.": "No se pare en carriles de transito ni brinde atencion medica invasiva.",
    "Move to a safe, public, well-lit place.": "Vaya a un lugar seguro, publico y bien iluminado.",
    "Stay with trusted people and preserve distance.": "Permanezca con personas de confianza y mantenga distancia.",
    "Do not confront, pursue, or try to detain anyone.": "No confronte, persiga ni intente detener a nadie.",
    "Stay far away from downed wires and anything touching them.": "Mantengase muy lejos de cables caidos y de cualquier cosa que los toque.",
    "Stay far away from wires and anything touching them. Warn others from a distance.": "Mantengase muy lejos de cables y de cualquier cosa que los toque. Avise a otras personas desde una distancia segura.",
    "Warn others from a distance.": "Avise a otras personas desde una distancia segura.",
    "Do not touch wires, poles, flooded areas, or affected vehicles.": "No toque cables, postes, zonas inundadas ni vehiculos afectados.",
    "Avoid contact with suspicious water.": "Evite el contacto con agua sospechosa.",
    "Document location, odor, color, weather, and visible organisms from a safe distance.": "Documente ubicacion, olor, color, clima y organismos visibles desde una distancia segura.",
    "Do not claim a cause or exact contaminant without lab or agency confirmation.": "No afirme una causa o contaminante exacto sin confirmacion de laboratorio o autoridad.",
    "Record lichen type, abundance, distance from road, weather, and photo context.": "Registre tipo de liquen, abundancia, distancia a la calle, clima y contexto de la foto.",
    "Compare with a cleaner reference site.": "Compare con un sitio de referencia mas limpio.",
    "Do not overclaim exact air quality or diagnose health impacts from lichen alone.": "No exagere conclusiones sobre calidad del aire ni diagnostique impactos en salud solo con liquenes.",
    "Move away from any immediate hazard.": "Alejese de cualquier peligro inmediato.",
    "Share only safe, non-private details.": "Comparta solo detalles seguros y no privados.",
    "Do not enter unsafe areas to gather more information.": "No entre en zonas inseguras para obtener mas informacion.",
    "Map repeat flood points.": "Mapee puntos recurrentes de inundacion.",
    "Pre-stage sandbags, detour signs, and utility contact lists.": "Prepare bolsas de arena, senales de desvio y listas de contacto de servicios.",
    "Check evacuation routes.": "Revise rutas de evacuacion.",
    "Keep alarms, extinguishers, and assembly points maintained.": "Mantenga alarmas, extintores y puntos de encuentro.",
    "Create a local emergency contact list.": "Cree una lista local de contactos de emergencia.",
    "Practice reporting using structured fields.": "Practique reportes con campos estructurados.",
}


SPANISH_RESOURCES: dict[str, str] = {
    "Emergency services": "Emergencias generales",
    "Police": "Policia",
    "Police / emergency services": "Policia / emergencias",
    "emergency management": "gestion de emergencias",
    "utility crew": "cuadrilla de servicios publicos",
    "utility emergency crew": "cuadrilla de emergencia electrica",
    "road crew": "equipo vial",
    "rescue": "rescate",
    "fire service": "bomberos",
    "medical responders": "respuesta medica",
    "building management": "administracion del edificio",
    "traffic control": "control de transito",
    "law enforcement": "autoridad policial",
    "victim support": "apoyo a victimas",
    "nearby safe site": "sitio seguro cercano",
    "environmental agency": "autoridad ambiental",
    "public works": "obras publicas",
    "community science coordinator": "coordinacion de ciencia ciudadana",
    "environmental health": "salud ambiental",
    "air quality agency": "autoridad de calidad del aire",
    "human reviewer": "revisor humano",
}


class TranslationAgent:
    name = "TranslationAgent"

    def run(self, result: MaydaIQResult, target_language: str) -> MaydaIQResult:
        if target_language == "English":
            return result

        trace = list(result.agent_trace)
        if target_language == "Spanish":
            translated_plan = self._translate_plan_to_spanish(result.action_plan)
            translated_packet = result.responder_packet.model_copy(
                update={
                    "immediate_actions": [self._to_spanish(item) for item in result.responder_packet.immediate_actions],
                    "recommended_resources": [SPANISH_RESOURCES.get(item, item) for item in result.responder_packet.recommended_resources],
                }
            )
            trace.append(
                AgentTraceStep(
                    agent=self.name,
                    summary="Spanish safety output applied; Foundry brief is requested in Spanish when live.",
                )
            )
            return result.model_copy(
                update={
                    "action_plan": translated_plan,
                    "responder_packet": translated_packet,
                    "disclaimer": SPANISH_DISCLAIMER,
                    "agent_trace": trace,
                }
            )

        trace.append(
            AgentTraceStep(
                agent=self.name,
                summary=f"{target_language} translation unavailable in demo; English safety output retained.",
                status="fallback",
            )
        )
        return result.model_copy(update={"agent_trace": trace})

    @classmethod
    def _translate_plan_to_spanish(cls, plan: ActionPlan) -> ActionPlan:
        return plan.model_copy(
            update={
                "ai_brief": cls._to_spanish(plan.ai_brief),
                "situation_summary": cls._to_spanish(plan.situation_summary),
                "contact_recommendations": [cls._to_spanish(item) for item in plan.contact_recommendations],
                "do_now": [cls._to_spanish(item) for item in plan.do_now],
                "avoid": [cls._to_spanish(item) for item in plan.avoid],
                "call_or_escalate": [cls._to_spanish(item) for item in plan.call_or_escalate],
                "report_summary": cls._to_spanish(plan.report_summary),
                "step_by_step_plan": [cls._to_spanish(item) for item in plan.step_by_step_plan],
                "next_steps": [cls._to_spanish(item) for item in plan.next_steps],
                "prevention_suggestions": [cls._to_spanish(item) for item in plan.prevention_suggestions],
                "unknowns": [cls._to_spanish(item) for item in plan.unknowns],
            }
        )

    @staticmethod
    def _resource_pairs() -> list[tuple[str, str]]:
        return sorted(SPANISH_RESOURCES.items(), key=lambda item: len(item[0]), reverse=True)

    @staticmethod
    def _to_spanish(text: str) -> str:
        if text in SPANISH_TEXT:
            return SPANISH_TEXT[text]
        if text.startswith("Contact "):
            translated = text.replace("local emergency services", "servicios locales de emergencia")
            for english, spanish in TranslationAgent._resource_pairs():
                translated = translated.replace(english, spanish)
            return translated.replace("Contact ", "Contacte a ").replace(
                " now for immediate danger. Coordinate with ",
                " ahora ante peligro inmediato. Coordine con ",
            ).replace(" for ", " para ")
        if text.startswith("Call/contact now: "):
            translated = text
            for english, spanish in TranslationAgent._resource_pairs():
                translated = translated.replace(english, spanish)
            return translated.replace("Call/contact now: ", "Llame/contacte ahora: ")
        if text.startswith("1. Stabilize safety first: "):
            return text.replace("1. Stabilize safety first: ", "1. Estabilice la seguridad primero: ")
        if text.startswith("2. Keep people away from risky actions: "):
            return text.replace("2. Keep people away from risky actions: ", "2. Mantenga a las personas lejos de acciones riesgosas: ")
        if text.startswith("3. Capture responder-ready facts:"):
            return "3. Reuna datos utiles para respondedores: hora, ubicacion aproximada, peligros visibles, rutas afectadas y dudas pendientes."
        if text.startswith("4. Route review to: "):
            resources = text.removeprefix("4. Route review to: ").rstrip(".").split(", ")
            translated = [SPANISH_RESOURCES.get(resource, resource) for resource in resources]
            return "4. Derive la revision a: " + ", ".join(translated) + "."
        return text
